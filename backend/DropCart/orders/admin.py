from django.contrib import admin
from .models import Order, OrderStateTransition


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "reservation",
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
        "user__email",
        "reservation__id",
        "reservation__drop__name",
    )

    readonly_fields = (
        "reservation",
        "user",
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
        "user",
        "reservation",
        "reservation__drop",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OrderStateTransition)
class OrderStateTransitionAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "order",
        "from_status",
        "to_status",
        "source",
        "created_at",
    )

    list_filter = (
        "from_status",
        "to_status",
        "source",
        "created_at",
    )

    search_fields = (
        "order__id",
        "order__user__email",
        "source",
    )

    readonly_fields = (
        "order",
        "from_status",
        "to_status",
        "source",
        "created_at",
    )

    ordering = (
        "-created_at",
    )

    list_per_page = 50

    list_select_related = (
        "order",
        "order__user",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False