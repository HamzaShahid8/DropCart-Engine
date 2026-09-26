from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Drop(models.Model):

    name = models.CharField(max_length=255)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    currency = models.CharField(
        max_length=3,
        default="USD",
    )
    total_stock = models.PositiveIntegerField()
    available_stock = models.PositiveIntegerField()
    starts_at = models.DateTimeField()

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-starts_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(total_stock__gte=0),
                name="drop_total_stock_gte_zero",
            ),
            models.CheckConstraint(
                condition=Q(available_stock__gte=0),
                name="drop_available_stock_gte_zero",
            ),
            models.CheckConstraint(
                condition=Q(
                    available_stock__lte=models.F("total_stock")
                ),
                name="drop_available_stock_lte_total_stock",
            ),
        ]

    def __str__(self):
        return self.name


class Reservation(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        CONSUMED = "consumed", "Consumed"

    drop = models.ForeignKey(
        Drop,
        on_delete=models.PROTECT,
        related_name="reservations",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reservations",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["drop", "status"],
                name="reservation_drop_status_idx",
            ),
            models.Index(
                fields=["expires_at"],
                name="reservation_expires_at_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["drop", "user"],
                condition=Q(status="active"),
                name="unique_active_reservation_per_user_drop",
            ),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.drop.name}"

    @property
    def is_expired(self):
        return (
            self.status == self.Status.ACTIVE
            and self.expires_at <= timezone.now()
        )