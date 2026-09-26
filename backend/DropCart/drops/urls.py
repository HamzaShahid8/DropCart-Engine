from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CreateReservationAPIView,
    DropViewSet,
    health_check,
)


router = DefaultRouter()

router.register(
    "drops",
    DropViewSet,
    basename="drop",
)


urlpatterns = [
    path(
        "",
        include(router.urls),
    ),
    path(
        "drops/<int:drop_id>/reserve/",
        CreateReservationAPIView.as_view(),
        name="create-reservation",
    ),
    path(
        "drops/<int:pk>/restore/",
        DropViewSet.as_view(
            {
                "post": "restore",
            }
        ),
        name="restore-drop",
    ),
    path("health/", health_check),
]