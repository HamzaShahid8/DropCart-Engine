import json
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from celery import shared_task
from django.conf import settings

from .gateway import MockPaymentGateway
from .models import Payment


def send_webhook(
    *,
    payment_id,
    event_type,
    event_id=None,
):
    gateway = MockPaymentGateway()

    webhook = gateway.create_webhook(
        payment_id=payment_id,
        event_type=event_type,
        event_id=event_id,
    )

    payload = {
        "event_id": webhook.event_id,
        "event_type": webhook.event_type,
        "payment_id": webhook.payment_id,
        "timestamp": webhook.timestamp,
    }

    body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    request = Request(
        settings.WEBHOOK_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": webhook.signature,
        },
        method="POST",
    )

    try:
        with urlopen(
            request,
            timeout=10,
        ) as response:
            return response.status

    except HTTPError as exc:
        error_body = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"Webhook returned HTTP {exc.code}: "
            f"{error_body}"
        ) from exc

    except URLError as exc:
        raise RuntimeError(
            f"Webhook connection failed: "
            f"{exc.reason}"
        ) from exc


@shared_task
def send_payment_webhook(
    *,
    payment_id,
    event_type=None,
):
    payment = Payment.objects.get(
        id=payment_id,
    )

    gateway = MockPaymentGateway()

    if event_type is None:
        event_type = (
            gateway.get_payment_result()
        )

    delay = gateway.get_webhook_delay()

    if delay > 0:
        time.sleep(delay)

    return send_webhook(
        payment_id=payment.gateway_payment_id,
        event_type=event_type,
    )


@shared_task
def send_duplicate_webhooks(
    *,
    payment_id,
    event_type="payment_succeeded",
):
    event_id = (
        f"evt_{payment_id}_"
        f"{uuid.uuid4().hex}"
    )

    results = []

    for _ in range(3):
        try:
            result = send_webhook(
                payment_id=payment_id,
                event_type=event_type,
                event_id=event_id,
            )

            results.append(
                {
                    "event": event_type,
                    "status": result,
                }
            )

        except RuntimeError as exc:
            results.append(
                {
                    "event": event_type,
                    "error": str(exc),
                }
            )

    return results


@shared_task
def send_out_of_order_webhooks(
    *,
    payment_id,
):
    results = []

    # First event:
    # payment_failed
    try:
        result = send_webhook(
            payment_id=payment_id,
            event_type="payment_failed",
        )

        results.append(
            {
                "event": "payment_failed",
                "status": result,
            }
        )

    except RuntimeError as exc:
        results.append(
            {
                "event": "payment_failed",
                "error": str(exc),
            }
        )

    # Second event:
    # payment_succeeded
    #
    # This should be rejected because
    # the payment has already failed.
    try:
        result = send_webhook(
            payment_id=payment_id,
            event_type="payment_succeeded",
        )

        results.append(
            {
                "event": "payment_succeeded",
                "status": result,
            }
        )

    except RuntimeError as exc:
        results.append(
            {
                "event": "payment_succeeded",
                "expected_rejection": True,
                "error": str(exc),
            }
        )

    return results