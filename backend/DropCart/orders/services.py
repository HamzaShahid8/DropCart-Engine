from django.db import transaction

from .models import Order, OrderStateTransition


class OrderTransitionError(Exception):
    pass


ALLOWED_TRANSITIONS = {
    Order.Status.RESERVED: {
        Order.Status.PAYMENT_PENDING,
        Order.Status.EXPIRED,
    },

    Order.Status.PAYMENT_PENDING: {
        Order.Status.PAID,
        Order.Status.FAILED,
        Order.Status.EXPIRED,
    },

    Order.Status.PAID: {
        Order.Status.CONFIRMED,
        Order.Status.REFUNDED,
    },

    Order.Status.CONFIRMED: {
        Order.Status.REFUNDED,
    },

    Order.Status.EXPIRED: {
        Order.Status.REFUNDED,
    },

    Order.Status.FAILED: set(),

    Order.Status.REFUNDED: set(),
}


@transaction.atomic
def create_order(
    *,
    reservation,
    user,
    amount,
    currency,
):
    order = Order.objects.create(
        reservation=reservation,
        user=user,
        amount=amount,
        currency=currency,
        status=Order.Status.RESERVED,
    )

    OrderStateTransition.objects.create(
        order=order,
        from_status=None,
        to_status=Order.Status.RESERVED,
        source="reservation",
    )

    return order


@transaction.atomic
def transition_order(
    *,
    order_id,
    to_status,
    source,
):
    order = (
        Order.objects
        .select_for_update()
        .get(id=order_id)
    )

    current_status = order.status

    allowed_statuses = ALLOWED_TRANSITIONS.get(
        current_status,
        set(),
    )

    if to_status not in allowed_statuses:
        raise OrderTransitionError(
            f"Invalid order transition: "
            f"{current_status} -> {to_status}"
        )

    order.status = to_status

    order.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    OrderStateTransition.objects.create(
        order=order,
        from_status=current_status,
        to_status=to_status,
        source=source,
    )

    return order