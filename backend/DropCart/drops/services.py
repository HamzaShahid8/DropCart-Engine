from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from orders.services import create_order
from .models import Drop, Reservation


class ReservationError(Exception):
    pass


class DropNotStartedError(ReservationError):
    pass


class SoldOutError(ReservationError):
    pass


class ActiveReservationExistsError(ReservationError):
    pass


@transaction.atomic
def create_drop(*, validated_data):
    return Drop.objects.create(
        **validated_data,
        available_stock=validated_data["total_stock"],
    )


@transaction.atomic
def update_drop(*, drop, validated_data):
    old_total_stock = drop.total_stock

    new_total_stock = validated_data.get(
        "total_stock",
        old_total_stock,
    )

    reserved_stock = (
        old_total_stock - drop.available_stock
    )

    if new_total_stock < reserved_stock:
        raise ReservationError(
            "Total stock cannot be less than already reserved stock."
        )

    if "total_stock" in validated_data:
        stock_difference = (
            new_total_stock - old_total_stock
        )

        drop.available_stock += stock_difference

    for field, value in validated_data.items():
        if field != "total_stock":
            setattr(drop, field, value)

    drop.total_stock = new_total_stock

    drop.save()

    return drop


@transaction.atomic
def delete_drop(*, drop):
    drop.is_deleted = True
    drop.deleted_at = timezone.now()

    drop.save(
        update_fields=[
            "is_deleted",
            "deleted_at",
            "updated_at",
        ]
    )


@transaction.atomic
def restore_drop(*, drop):
    drop.is_deleted = False
    drop.deleted_at = None

    drop.save(
        update_fields=[
            "is_deleted",
            "deleted_at",
            "updated_at",
        ]
    )

    return drop


@transaction.atomic
def create_reservation(*, drop_id, user):
    drop = (
        Drop.objects
        .select_for_update()
        .get(id=drop_id)
    )

    now = timezone.now()

    if drop.is_deleted:
        raise ReservationError(
            "This drop is no longer available."
        )

    if drop.starts_at > now:
        raise DropNotStartedError(
            "This drop has not started yet."
        )

    existing_reservation = Reservation.objects.filter(
        drop=drop,
        user=user,
        status=Reservation.Status.ACTIVE,
    ).first()

    if existing_reservation:
        raise ActiveReservationExistsError(
            "You already have an active reservation for this drop."
        )

    if drop.available_stock <= 0:
        raise SoldOutError(
            "This drop is sold out."
        )

    reservation = Reservation.objects.create(
        drop=drop,
        user=user,
        status=Reservation.Status.ACTIVE,
        expires_at=now + timedelta(minutes=5),
    )

    drop.available_stock -= 1

    drop.save(
        update_fields=[
            "available_stock",
            "updated_at",
        ]
    )

    create_order(
        reservation=reservation,
        user=user,
        amount=drop.price,
        currency=drop.currency,
    )

    return reservation