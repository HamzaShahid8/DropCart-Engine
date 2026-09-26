from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import User
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    RefreshTokenSerializer,
    RegisterSerializer,
    UserSerializer,
)

class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        if User.objects.filter(email=email).exists():
            return Response(
                {
                    "error": "EMAIL_ALREADY_EXISTS",
                    "message": "A user with this email already exists.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            email=email,
            password=serializer.validated_data["password"],
            first_name=serializer.validated_data.get("first_name", ""),
            last_name=serializer.validated_data.get("last_name", ""),
        )

        return Response(
            {
                "message": "User registered successfully.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )
        
class LoginAPIView(APIView):

    permission_classes = [
        AllowAny
    ]

    def post(self, request):

        serializer = LoginSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        email = serializer.validated_data[
            "email"
        ].lower()

        password = serializer.validated_data[
            "password"
        ]

        user = User.objects.filter(
            email=email
        ).first()

        if not user or not user.check_password(
            password
        ):

            return Response(
                {
                    "error": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:

            return Response(
                {
                    "error": "USER_INACTIVE",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(
                    refresh.access_token
                ),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )
        
class RefreshTokenAPIView(APIView):

    permission_classes = [
        AllowAny
    ]

    def post(self, request):

        serializer = RefreshTokenSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        refresh_token = serializer.validated_data[
            "refresh"
        ]

        try:

            refresh = RefreshToken(
                refresh_token
            )

            access_token = refresh.access_token

            return Response(
                {
                    "access": str(
                        access_token
                    ),
                },
                status=status.HTTP_200_OK,
            )

        except Exception:

            return Response(
                {
                    "error": "INVALID_REFRESH_TOKEN",
                    "message": "Refresh token is invalid or expired.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
            
class LogoutAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):

        serializer = LogoutSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:

            refresh = RefreshToken(
                serializer.validated_data[
                    "refresh"
                ]
            )

            refresh.blacklist()

        except Exception:

            return Response(
                {
                    "error": "INVALID_REFRESH_TOKEN",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "Logged out successfully."
            },
            status=status.HTTP_200_OK,
        )
        
class ChangePasswordAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):

        serializer = ChangePasswordSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        current_password = serializer.validated_data[
            "current_password"
        ]

        new_password = serializer.validated_data[
            "new_password"
        ]

        if not request.user.check_password(
            current_password
        ):

            return Response(
                {
                    "error": "INVALID_CURRENT_PASSWORD",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(
            new_password
        )

        request.user.save(
            update_fields=[
                "password",
                "updated_at",
            ]
        )

        return Response(
            {
                "message": "Password changed successfully."
            },
            status=status.HTTP_200_OK,
        )
        
class DashboardAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        return Response(
            {
                "message": "Welcome to DropCart dashboard.",
                "user": UserSerializer(
                    request.user
                ).data,
            },
            status=status.HTTP_200_OK,
        )
        
class MeAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        return Response(
            UserSerializer(
                request.user
            ).data,
            status=status.HTTP_200_OK,
        )