from django.conf import settings
from django.db import models
from drops.models import Reservation


class Order(models.Model):

    class Status(models.TextChoices):
        RESERVED = "reserved", "Reserved"
        PAYMENT_PENDING = "payment_pending", "Payment Pending"
        PAID = "paid", "Paid"
        CONFIRMED = "confirmed", "Confirmed"
        FAILED = "failed", "Failed"
        EXPIRED = "expired", "Expired"
        REFUNDED = "refunded", "Refunded"

    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.PROTECT,
        related_name="order",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    currency = models.CharField(
        max_length=3,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.RESERVED,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "status"],
                name="order_user_status_idx",
            ),
            models.Index(
                fields=["status"],
                name="order_status_idx",
            ),
        ]

    def __str__(self):
        return f"Order #{self.id} - {self.status}"
    
    
class OrderStateTransition(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="state_transitions",
    )

    from_status = models.CharField(
        max_length=30,
        null=True,
        blank=True,
    )

    to_status = models.CharField(
        max_length=30,
    )

    source = models.CharField(
        max_length=50,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(
                fields=["order", "created_at"],
                name="order_transition_idx",
            ),
        ]

    def __str__(self):
        return (
            f"Order #{self.order_id}: "
            f"{self.from_status} → {self.to_status}"
        )