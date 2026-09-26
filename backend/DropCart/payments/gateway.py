import hashlib
import hmac
import json
import random
import time
import uuid
from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings


class GatewayError(Exception):
    pass


@dataclass(frozen=True)
class PaymentIntent:
    payment_id: str
    amount: Decimal
    currency: str
    status: str


@dataclass(frozen=True)
class WebhookPayload:
    event_id: str
    event_type: str
    payment_id: str
    timestamp: int
    signature: str


@dataclass(frozen=True)
class RefundResult:
    refund_id: str
    payment_id: str
    status: str


class MockPaymentGateway:

    def create_payment_intent(
        self,
        *,
        amount,
        currency,
        idempotency_key,
    ):
        if not idempotency_key:
            raise GatewayError(
                "Gateway idempotency key is required."
            )

        payment_id = (
            f"mock_pay_{uuid.uuid4().hex}"
        )

        return PaymentIntent(
            payment_id=payment_id,
            amount=amount,
            currency=currency,
            status="pending",
        )

    def get_payment_result(self):
        """
        Simulate the payment gateway result.

        Around 10% of payments fail.
        Around 90% succeed.
        """

        if random.random() < 0.10:
            return "payment_failed"

        return "payment_succeeded"

    def get_webhook_delay(self):
        """
        Simulate random webhook delivery delay
        between 0 and 30 seconds.
        """

        return random.randint(0, 30)

    def refund_payment(
        self,
        *,
        payment_id,
    ):
        """
        Simulate a payment refund.

        Used when a payment succeeds after
        the reservation/order has already expired.
        """

        if not payment_id:
            raise GatewayError(
                "Payment ID is required for refund."
            )

        refund_id = (
            f"mock_refund_{uuid.uuid4().hex}"
        )

        return RefundResult(
            refund_id=refund_id,
            payment_id=payment_id,
            status="refunded",
        )

    def create_webhook(
        self,
        *,
        payment_id,
        event_type,
        event_id=None,
        timestamp=None,
    ):
        """
        Create a signed webhook payload.

        The exact JSON bytes used here for the
        HMAC signature are also used by the task
        when sending the webhook request.
        """

        secret = settings.WEBHOOK_SECRET

        if not secret:
            raise GatewayError(
                "Webhook secret is not configured."
            )

        event_id = (
            event_id
            or f"evt_{uuid.uuid4().hex}"
        )

        timestamp = (
            timestamp
            or int(time.time())
        )

        payload = {
            "event_id": event_id,
            "event_type": event_type,
            "payment_id": payment_id,
            "timestamp": timestamp,
        }

        payload_bytes = json.dumps(
            payload,
            separators=(",", ":"),
        ).encode("utf-8")

        signature = hmac.new(
            secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()

        return WebhookPayload(
            event_id=event_id,
            event_type=event_type,
            payment_id=payment_id,
            timestamp=timestamp,
            signature=signature,
        )