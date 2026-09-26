from django.urls import path

from .views import (
    ChangePasswordAPIView,
    DashboardAPIView,
    LoginAPIView,
    LogoutAPIView,
    MeAPIView,
    RefreshTokenAPIView,
    RegisterAPIView,
)


urlpatterns = [

    path(
        "register/",
        RegisterAPIView.as_view(),
        name="register",
    ),

    path(
        "login/",
        LoginAPIView.as_view(),
        name="login",
    ),

    path(
        "refresh/",
        RefreshTokenAPIView.as_view(),
        name="refresh",
    ),

    path(
        "logout/",
        LogoutAPIView.as_view(),
        name="logout",
    ),

    path(
        "change-password/",
        ChangePasswordAPIView.as_view(),
        name="change-password",
    ),

    path(
        "dashboard/",
        DashboardAPIView.as_view(),
        name="dashboard",
    ),

    path(
        "me/",
        MeAPIView.as_view(),
        name="me",
    ),
]