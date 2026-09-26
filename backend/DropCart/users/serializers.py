from rest_framework import serializers

from .models import User


class RegisterSerializer(serializers.Serializer):

    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    first_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )

    last_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )


class LoginSerializer(serializers.Serializer):

    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True,
    )


class RefreshTokenSerializer(serializers.Serializer):

    refresh = serializers.CharField(
        write_only=True,
    )


class LogoutSerializer(serializers.Serializer):

    refresh = serializers.CharField(
        write_only=True,
    )


class ChangePasswordSerializer(serializers.Serializer):

    current_password = serializers.CharField(
        write_only=True,
    )

    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    def validate(self, attrs):

        if (
            attrs["current_password"]
            == attrs["new_password"]
        ):
            raise serializers.ValidationError(
                "New password must be different from current password."
            )

        return attrs


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User

        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "email",
            "created_at",
        ]