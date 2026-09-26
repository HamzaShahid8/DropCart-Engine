import hashlib
import hmac
import time
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from orders.models import Order
from orders.services import (
    OrderTransitionError,
    transition_order,
)
from payments.gateway import (
    GatewayError,
    MockPaymentGateway,
)
from payments.models import Payment
from .models import WebhookEvent


class WebhookSecurityError(Exception):
    pass


class WebhookProcessingError(Exception):
    pass


def verify_webhook_signature(
    *,
    raw_body,
    signature,
):
    if not signature:
        raise WebhookSecurityError(
            "Webhook signature is required."
        )

    secret = settings.WEBHOOK_SECRET

    if not secret:
        raise WebhookSecurityError(
            "Webhook secret is not configured."
        )

    expected_signature = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(
        expected_signature,
        signature,
    ):
        raise WebhookSecurityError(
            "Invalid webhook signature."
        )

    return True


def validate_webhook_timestamp(timestamp):
    try:
        timestamp = float(timestamp)
    except (TypeError, ValueError):
        raise WebhookSecurityError(
            "Invalid webhook timestamp."
        )

    current_time = time.time()
    age = current_time - timestamp

    if age > 300:
        raise WebhookSecurityError(
            "Webhook event is older than 5 minutes."
        )

    if age < -300:
        raise WebhookSecurityError(
            "Webhook timestamp is too far in the future."
        )

    return True


@transaction.atomic
def process_payment_webhook(
    *,
    webhook_event,
):
    event_type = webhook_event.event_type
    payment_id = webhook_event.payment_id

    if not payment_id:
        raise WebhookProcessingError(
            "payment_id is required."
        )

    try:
        payment = (
            Payment.objects
            .select_for_update()
            .select_related("order")
            .get(
                gateway_payment_id=payment_id,
            )
        )
    except Payment.DoesNotExist:
        raise WebhookProcessingError(
            "Payment not found."
        )

    order = (
        Order.objects
        .select_for_update()
        .get(
            id=payment.order_id,
        )
    )

    if event_type == "payment_succeeded":
        return process_payment_succeeded(
            payment=payment,
            order=order,
        )

    if event_type == "payment_failed":
        return process_payment_failed(
            payment=payment,
            order=order,
        )

    webhook_event.status = WebhookEvent.Status.IGNORED
    webhook_event.processed_at = timezone.now()

    webhook_event.save(
        update_fields=[
            "status",
            "processed_at",
        ]
    )

    return order


def process_payment_succeeded(
    *,
    payment,
    order,
):
    if payment.status == Payment.Status.SUCCEEDED:
        return order

    if payment.status == Payment.Status.REFUNDED:
        return order

    if payment.status == Payment.Status.FAILED:
        raise WebhookProcessingError(
            "Payment cannot be marked as succeeded "
            f"from status '{payment.status}'."
        )

    # Normal successful payment.
    if order.status == Order.Status.PAYMENT_PENDING:

        payment.status = Payment.Status.SUCCEEDED

        payment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        try:
            transition_order(
                order_id=order.id,
                to_status=Order.Status.PAID,
                source="webhook",
            )
        except OrderTransitionError as exc:
            raise WebhookProcessingError(
                str(exc)
            ) from exc

        return order

    # Payment succeeded after reservation expired.
    if order.status == Order.Status.EXPIRED:

        gateway = MockPaymentGateway()

        try:
            refund_result = gateway.refund_payment(
                payment_id=payment.gateway_payment_id,
            )
        except GatewayError as exc:
            raise WebhookProcessingError(
                f"Payment refund failed: {exc}"
            ) from exc

        try:
            transition_order(
                order_id=order.id,
                to_status=Order.Status.REFUNDED,
                source="webhook_late_payment",
            )
        except OrderTransitionError as exc:
            raise WebhookProcessingError(
                str(exc)
            ) from exc

        payment.status = Payment.Status.REFUNDED
        payment.refund_id = refund_result.refund_id

        payment.save(
            update_fields=[
                "status",
                "refund_id",
                "updated_at",
            ]
        )

        return order

    if order.status in {
        Order.Status.PAID,
        Order.Status.CONFIRMED,
    }:
        return order

    raise WebhookProcessingError(
        "Order cannot be marked as paid from "
        f"status '{order.status}'."
    )


def process_payment_failed(
    *,
    payment,
    order,
):
    if payment.status == Payment.Status.FAILED:
        return order

    if payment.status in {
        Payment.Status.SUCCEEDED,
        Payment.Status.REFUNDED,
    }:
        raise WebhookProcessingError(
            "Payment cannot be marked as failed "
            f"from status '{payment.status}'."
        )

    payment.status = Payment.Status.FAILED

    payment.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    if order.status == Order.Status.PAYMENT_PENDING:
        try:
            transition_order(
                order_id=order.id,
                to_status=Order.Status.FAILED,
                source="webhook",
            )
        except OrderTransitionError as exc:
            raise WebhookProcessingError(
                str(exc)
            ) from exc

    elif order.status in {
        Order.Status.FAILED,
        Order.Status.EXPIRED,
    }:
        pass

    elif order.status in {
        Order.Status.PAID,
        Order.Status.CONFIRMED,
    }:
        raise WebhookProcessingError(
            "Payment failure cannot move an already "
            "successful order backwards."
        )

    else:
        raise WebhookProcessingError(
            "Order cannot be marked as failed from "
            f"status '{order.status}'."
        )

    return order