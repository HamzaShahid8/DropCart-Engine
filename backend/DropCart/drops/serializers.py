from rest_framework import serializers
from .models import Drop, Reservation


class DropSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drop
        fields = [
            "id",
            "name",
            "price",
            "currency",
            "total_stock",
            "available_stock",
            "starts_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "available_stock",
            "created_at",
        ]


class ReservationSerializer(serializers.ModelSerializer):
    drop_name = serializers.CharField(
        source="drop.name",
        read_only=True,
    )

    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    class Meta:
        model = Reservation
        fields = [
            "id",
            "drop",
            "drop_name",
            "user_email",
            "status",
            "expires_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "drop_name",
            "user_email",
            "status",
            "expires_at",
            "created_at",
        ]