"""Management command to retry failed sentiment analysis.

Usage:
    python manage.py retry_failed_sentiment
    python manage.py retry_failed_sentiment --limit 50
"""

from django.core.management.base import BaseCommand

from feedback.services.sentiment import retry_failed_analyses


class Command(BaseCommand):
    help = "Re-run sentiment analysis for all failed feedback records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximum number of failed records to retry.",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        processed, succeeded, failed = retry_failed_analyses(limit=limit)

        self.stdout.write(
            f"Retry complete: {processed} processed, "
            f"{succeeded} succeeded, {failed} failed."
        )
