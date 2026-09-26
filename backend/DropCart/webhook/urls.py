from django.urls import path

from .views import PaymentWebhookAPIView


urlpatterns = [
    path(
        "payment/",
        PaymentWebhookAPIView.as_view(),
        name="payment-webhook",
    ),
]