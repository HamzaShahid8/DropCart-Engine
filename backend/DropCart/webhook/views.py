import json

from django.db import IntegrityError
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import WebhookEvent
from .services import (
    WebhookProcessingError,
    WebhookSecurityError,
    process_payment_webhook,
    validate_webhook_timestamp,
    verify_webhook_signature,
)


class PaymentWebhookAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        raw_body = request.body

        signature = request.headers.get(
            "X-Webhook-Signature"
        )

        # 1. Verify HMAC signature
        try:
            verify_webhook_signature(
                raw_body=raw_body,
                signature=signature,
            )

        except WebhookSecurityError as exc:
            return Response(
                {
                    "error": "INVALID_WEBHOOK_SIGNATURE",
                    "message": str(exc),
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # 2. Parse JSON payload
        try:
            payload = json.loads(raw_body)

        except json.JSONDecodeError:
            return Response(
                {
                    "error": "INVALID_WEBHOOK_PAYLOAD",
                    "message": "Webhook body must be valid JSON.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. Extract webhook fields
        event_id = payload.get("event_id")
        event_type = payload.get("event_type")
        payment_id = payload.get("payment_id")
        timestamp = payload.get("timestamp")

        # 4. Validate required fields
        if not event_id or not event_type:
            return Response(
                {
                    "error": "INVALID_WEBHOOK_PAYLOAD",
                    "message": "event_id and event_type are required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if timestamp is None:
            return Response(
                {
                    "error": "INVALID_WEBHOOK_PAYLOAD",
                    "message": "timestamp is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 5. Validate timestamp
        try:
            validate_webhook_timestamp(timestamp)

        except WebhookSecurityError as exc:
            return Response(
                {
                    "error": "INVALID_WEBHOOK_TIMESTAMP",
                    "message": str(exc),
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # 6. Check duplicate event
        existing_event = WebhookEvent.objects.filter(
            event_id=event_id,
        ).first()

        if existing_event:
            return Response(
                {
                    "message": "Webhook event already processed.",
                    "event_id": event_id,
                    "status": existing_event.status,
                },
                status=status.HTTP_200_OK,
            )

        # 7. Store webhook event
        try:
            webhook_event = WebhookEvent.objects.create(
                event_id=event_id,
                event_type=event_type,
                payment_id=payment_id,
                payload=payload,
                status=WebhookEvent.Status.RECEIVED,
            )

        except IntegrityError:
            # Handles concurrent duplicate webhook requests.
            existing_event = WebhookEvent.objects.get(
                event_id=event_id,
            )

            return Response(
                {
                    "message": "Webhook event already processed.",
                    "event_id": event_id,
                    "status": existing_event.status,
                },
                status=status.HTTP_200_OK,
            )

        # 8. Process payment webhook
        try:
            process_payment_webhook(
                webhook_event=webhook_event,
            )

        except WebhookProcessingError as exc:
            webhook_event.status = WebhookEvent.Status.FAILED
            webhook_event.error_message = str(exc)

            webhook_event.save(
                update_fields=[
                    "status",
                    "error_message",
                ]
            )

            return Response(
                {
                    "error": "WEBHOOK_PROCESSING_FAILED",
                    "message": str(exc),
                    "event_id": event_id,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 9. Mark webhook as processed
        webhook_event.status = WebhookEvent.Status.PROCESSED
        webhook_event.processed_at = timezone.now()

        webhook_event.save(
            update_fields=[
                "status",
                "processed_at",
            ]
        )

        return Response(
            {
                "message": "Webhook processed successfully.",
                "event_id": event_id,
            },
            status=status.HTTP_200_OK,
        )