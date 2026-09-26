from django.core.management.base import BaseCommand, CommandError
from payments.models import Payment
from payments.tasks import (
    send_duplicate_webhooks,
    send_out_of_order_webhooks,
)


class Command(BaseCommand):

    help = (
        "Test duplicate and out-of-order payment webhooks."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "scenario",
            choices=[
                "duplicate",
                "out-of-order",
            ],
        )

        parser.add_argument(
            "payment_id",
            type=int,
        )

    def handle(self, *args, **options):
        scenario = options["scenario"]
        payment_id = options["payment_id"]

        try:
            payment = Payment.objects.get(
                id=payment_id,
            )
        except Payment.DoesNotExist:
            raise CommandError(
                f"Payment {payment_id} does not exist."
            )

        self.stdout.write(
            f"Testing '{scenario}' scenario "
            f"for Payment #{payment.id}"
        )

        if scenario == "duplicate":
            task = send_duplicate_webhooks.delay(
                payment_id=payment.gateway_payment_id,
                event_type="payment_succeeded",
            )

        else:
            task = send_out_of_order_webhooks.delay(
                payment_id=payment.gateway_payment_id,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Webhook test queued successfully. "
                f"Task ID: {task.id}"
            )
        )