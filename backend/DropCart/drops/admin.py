from django.contrib import admin

from .models import Drop, Reservation
from .services import restore_drop


@admin.register(Drop)
class DropAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "price",
        "currency",
        "total_stock",
        "available_stock",
        "starts_at",
        "is_deleted",
        "deleted_at",
        "created_at",
    )

    list_filter = (
        "is_deleted",
        "currency",
        "starts_at",
        "created_at",
    )

    search_fields = (
        "name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "deleted_at",
    )

    ordering = (
        "-created_at",
    )

    list_per_page = 25

    actions = [
        "restore_drops",
    ]

    @admin.action(description="Restore selected drops")
    def restore_drops(self, request, queryset):

        restored_count = 0

        for drop in queryset.filter(is_deleted=True):
            restore_drop(drop=drop)
            restored_count += 1

        self.message_user(
            request,
            f"{restored_count} drop(s) restored successfully.",
        )


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "drop",
        "status",
        "expires_at",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
        "expires_at",
    )

    search_fields = (
        "user__email",
        "drop__name",
    )

    readonly_fields = (
        "drop",
        "user",
        "status",
        "expires_at",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    list_per_page = 25