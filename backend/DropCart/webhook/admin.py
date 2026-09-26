from django.contrib import admin
from .models import WebhookEvent


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "event_id",
        "event_type",
        "payment_id",
        "status",
        "received_at",
        "processed_at",
    )

    list_filter = (
        "event_type",
        "status",
        "received_at",
    )

    search_fields = (
        "event_id",
        "event_type",
        "payment_id",
    )

    readonly_fields = (
        "event_id",
        "event_type",
        "payment_id",
        "payload",
        "status",
        "error_message",
        "received_at",
        "processed_at",
    )

    ordering = ("-received_at",)

    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False