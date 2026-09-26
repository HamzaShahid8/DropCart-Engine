from django.db import models


class WebhookEvent(models.Model):

    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        PROCESSED = "processed", "Processed"
        FAILED = "failed", "Failed"
        IGNORED = "ignored", "Ignored"

    event_id = models.CharField(
        max_length=255,
        unique=True,
    )

    event_type = models.CharField(
        max_length=100,
    )

    payment_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    payload = models.JSONField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RECEIVED,
    )

    error_message = models.TextField(
        blank=True,
        null=True,
    )

    received_at = models.DateTimeField(
        auto_now_add=True,
    )

    processed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-received_at"]

        indexes = [
            models.Index(
                fields=["event_type"],
                name="webhook_event_type_idx",
            ),
            models.Index(
                fields=["status"],
                name="webhook_status_idx",
            ),
            models.Index(
                fields=["payment_id"],
                name="webhook_payment_id_idx",
            ),
            models.Index(
                fields=["received_at"],
                name="webhook_received_at_idx",
            ),
        ]

    def __str__(self):
        return f"{self.event_id} - {self.event_type}"