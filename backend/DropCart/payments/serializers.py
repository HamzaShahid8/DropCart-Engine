from rest_framework import serializers
from .models import Payment


class PaymentOrderSerializer(serializers.Serializer):

    id = serializers.IntegerField()
    status = serializers.CharField()


class CheckoutSerializer(serializers.Serializer):
    pass


class PaymentReadSerializer(serializers.ModelSerializer):

    order = PaymentOrderSerializer(
        read_only=True,
    )

    class Meta:
        model = Payment

        fields = [
            "id",
            "order",
            "gateway_payment_id",
            "refund_id",
            "amount",
            "currency",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields