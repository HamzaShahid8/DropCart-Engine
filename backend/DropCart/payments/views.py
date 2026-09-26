from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import (
    CheckoutError,
    IdempotencyKeyError,
    InvalidOrderStatusError,
    create_checkout,
)


class CheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        idempotency_key = request.headers.get("Idempotency-Key")

        if not idempotency_key:
            return Response(
                {
                    "error": "IDEMPOTENCY_KEY_REQUIRED",
                    "message": "Idempotency-Key header is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            response_status, response_body = create_checkout(
                order_id=order_id,
                user=request.user,
                idempotency_key=idempotency_key,
            )

        except ObjectDoesNotExist:
            return Response(
                {
                    "error": "ORDER_NOT_FOUND",
                    "message": "Order not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except InvalidOrderStatusError as exc:
            return Response(
                {
                    "error": "INVALID_ORDER_STATUS",
                    "message": str(exc),
                },
                status=status.HTTP_409_CONFLICT,
            )

        except IdempotencyKeyError as exc:
            return Response(
                {
                    "error": "IDEMPOTENCY_KEY_REQUIRED",
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except CheckoutError as exc:
            return Response(
                {
                    "error": "CHECKOUT_FAILED",
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            response_body,
            status=response_status,
        )