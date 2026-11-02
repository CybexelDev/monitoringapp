"""Process Admin due reminders independently of Admin page visits."""
import time

from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from monitoringapp.views import _process_admin_reminders


class Command(BaseCommand):
    help = "Process Admin reminders that have reached their reminder time."

    def add_arguments(self, parser):
        parser.add_argument("--watch", action="store_true")
        parser.add_argument("--interval", type=int, default=15)

    def handle(self, *args, **options):
        interval = options["interval"]
        if interval < 1:
            raise CommandError("--interval must be at least 1 second.")

        while True:
            try:
                close_old_connections()
                count = _process_admin_reminders()
                if count or not options["watch"]:
                    self.stdout.write(f"Created {count} Admin due reminder notification(s).")
            finally:
                close_old_connections()
            if not options["watch"]:
                break
            try:
                time.sleep(interval)
            except KeyboardInterrupt:
                self.stdout.write("Admin reminder worker stopped.")
                break
