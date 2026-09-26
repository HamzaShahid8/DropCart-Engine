import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Create superuser from environment variables."

    def handle(self, *args, **kwargs):

        email = os.getenv("SUPERUSER_EMAIL")
        password = os.getenv("SUPERUSER_PASSWORD")

        if not email or not password:
            self.stdout.write(
                self.style.ERROR(
                    "SUPERUSER_EMAIL and SUPERUSER_PASSWORD are required."
                )
            )
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(
                    f"Superuser with email {email} already exists."
                )
            )
            return

        User.objects.create_superuser(
            email=email,
            password=password,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Superuser {email} created successfully."
            )
        )