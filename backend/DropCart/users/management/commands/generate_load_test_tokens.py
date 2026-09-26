import json
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken
from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = "Generate JWT access tokens for load-test users."

    def handle(self, *args, **options):
        users = User.objects.filter(
            email__startswith="loadtest"
        ).order_by("id")

        tokens = []

        for user in users:
            access_token = AccessToken.for_user(user)

            tokens.append(
                {
                    "user_id": user.id,
                    "email": user.email,
                    "token": str(access_token),
                }
            )

        output_file = settings.BASE_DIR / "load_test_tokens.json"

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(tokens, file, indent=2)

        self.stdout.write(
            self.style.SUCCESS(
                f"Generated tokens: {len(tokens)}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Saved to: {output_file}"
            )
        )