from django.contrib import admin

from .models import IdempotencyRecord, Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "order",
        "gateway_payment_id",
        "refund_id",
        "amount",
        "currency",
        "status",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "currency",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "id",
        "order__id",
        "order__user__email",
        "gateway_payment_id",
        "refund_id",
    )

    readonly_fields = (
        "order",
        "gateway_payment_id",
        "refund_id",
        "amount",
        "currency",
        "status",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    list_per_page = 25

    list_select_related = (
        "order",
        "order__user",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False


@admin.register(IdempotencyRecord)
class IdempotencyRecordAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "key",
        "order",
        "response_status",
        "created_at",
    )

    list_filter = (
        "response_status",
        "created_at",
    )

    search_fields = (
        "key",
        "order__id",
        "order__user__email",
    )

    readonly_fields = (
        "key",
        "order",
        "response_status",
        "response_body",
        "created_at",
    )

    ordering = (
        "-created_at",
    )

    list_per_page = 25

    list_select_related = (
        "order",
        "order__user",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False