from rest_framework import serializers

from .models import Order, OrderStateTransition


class OrderPaymentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    gateway_payment_id = serializers.CharField(
        allow_null=True,
    )
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    currency = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class OrderStateTransitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStateTransition
        fields = [
            "id",
            "from_status",
            "to_status",
            "source",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "from_status",
            "to_status",
            "source",
            "created_at",
        ]


class OrderSerializer(serializers.ModelSerializer):
    reservation_id = serializers.IntegerField(
        source="reservation.id",
        read_only=True,
    )

    payment = OrderPaymentSerializer(
        read_only=True,
    )

    state_transitions = OrderStateTransitionSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Order

        fields = [
            "id",
            "reservation_id",
            "amount",
            "currency",
            "status",
            "payment",
            "state_transitions",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "reservation_id",
            "amount",
            "currency",
            "status",
            "payment",
            "state_transitions",
            "created_at",
            "updated_at",
        ]