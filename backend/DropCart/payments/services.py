from django.db import transaction

from orders.models import Order
from orders.services import (
    OrderTransitionError,
    transition_order,
)

from .gateway import (
    GatewayError,
    MockPaymentGateway,
)
from .models import (
    IdempotencyRecord,
    Payment,
)
from .tasks import send_payment_webhook


class CheckoutError(Exception):
    pass


class IdempotencyKeyError(CheckoutError):
    pass


class InvalidOrderStatusError(CheckoutError):
    pass


@transaction.atomic
def create_checkout(
    *,
    order_id,
    user,
    idempotency_key,
):
    if not idempotency_key:
        raise IdempotencyKeyError(
            "Idempotency-Key header is required."
        )

    order = (
        Order.objects
        .select_for_update()
        .select_related("reservation")
        .get(
            id=order_id,
            user=user,
        )
    )

    existing_record = (
        IdempotencyRecord.objects
        .filter(
            key=idempotency_key,
            order=order,
        )
        .first()
    )

    if existing_record:
        return (
            existing_record.response_status,
            existing_record.response_body,
        )

    if order.status != Order.Status.RESERVED:
        raise InvalidOrderStatusError(
            f"Order cannot be checked out from "
            f"status '{order.status}'."
        )

    try:
        transition_order(
            order_id=order.id,
            to_status=Order.Status.PAYMENT_PENDING,
            source="checkout",
        )
    except OrderTransitionError as exc:
        raise CheckoutError(str(exc)) from exc

    payment = Payment.objects.create(
        order=order,
        amount=order.amount,
        currency=order.currency,
        status=Payment.Status.PENDING,
    )

    gateway = MockPaymentGateway()

    try:
        payment_intent = gateway.create_payment_intent(
            amount=payment.amount,
            currency=payment.currency,
            idempotency_key=idempotency_key,
        )
    except GatewayError as exc:
        raise CheckoutError(str(exc)) from exc

    payment.gateway_payment_id = (
        payment_intent.payment_id
    )

    payment.save(
        update_fields=[
            "gateway_payment_id",
            "updated_at",
        ]
    )

    response_body = {
        "order_id": order.id,
        "payment_id": payment.id,
        "gateway_payment_id": (
            payment.gateway_payment_id
        ),
        "status": payment.status,
        "amount": str(payment.amount),
        "currency": payment.currency,
    }

    response_status = 201

    IdempotencyRecord.objects.create(
        key=idempotency_key,
        order=order,
        response_status=response_status,
        response_body=response_body,
    )

    payment_id = payment.id

    transaction.on_commit(
        lambda: send_payment_webhook.delay(
            payment_id=payment_id,
        )
    )

    return response_status, response_body