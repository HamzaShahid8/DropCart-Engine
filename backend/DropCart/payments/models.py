from django.db import models

from orders.models import Order


class Payment(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name="payment",
    )

    gateway_payment_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    
    refund_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )

    currency = models.CharField(
        max_length=3,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
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
                fields=["status"],
                name="payment_status_idx",
            ),
        ]

    def __str__(self):
        return f"Payment #{self.id} - {self.status}"


class IdempotencyRecord(models.Model):

    key = models.CharField(
        max_length=255,
        unique=True,
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="idempotency_records",
    )

    response_status = models.PositiveSmallIntegerField()

    response_body = models.JSONField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["order"],
                name="idempotency_order_idx",
            ),
        ]

    def __str__(self):
        return self.key