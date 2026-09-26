from django.urls import path
from .views import CheckoutAPIView


urlpatterns = [
    path(
        "orders/<int:order_id>/checkout/",
        CheckoutAPIView.as_view(),
        name="order-checkout",
    ),
]