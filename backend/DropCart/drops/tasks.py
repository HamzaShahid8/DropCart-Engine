from celery import shared_task
from django.db import transaction
from django.utils import timezone
from orders.models import Order
from orders.services import transition_order
from .models import Drop, Reservation

@shared_task
def expire_reservations():
    now = timezone.now()

    expired_reservations = Reservation.objects.filter(
        status=Reservation.Status.ACTIVE,
        expires_at__lte=now,
    )

    expired_count = 0

    for reservation in expired_reservations:

        with transaction.atomic():

            locked_reservation = (
                Reservation.objects
                .select_for_update()
                .select_related("drop")
                .get(id=reservation.id)
            )

            if (
                locked_reservation.status
                != Reservation.Status.ACTIVE
            ):
                continue

            drop = (
                Drop.objects
                .select_for_update()
                .get(
                    id=locked_reservation.drop_id,
                )
            )

            locked_reservation.status = (
                Reservation.Status.EXPIRED
            )

            locked_reservation.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            drop.available_stock += 1

            drop.save(
                update_fields=[
                    "available_stock",
                    "updated_at",
                ]
            )

            order = (
                Order.objects
                .select_for_update()
                .get(
                    reservation=locked_reservation,
                )
            )

            if order.status in {
                Order.Status.RESERVED,
                Order.Status.PAYMENT_PENDING,
            }:
                transition_order(
                    order_id=order.id,
                    to_status=Order.Status.EXPIRED,
                    source="worker",
                )

            expired_count += 1

    return expired_count