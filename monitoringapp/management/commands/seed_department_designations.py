# Save as monitoringapp/management/commands/seed_department_designations.py
from django.core.management.base import BaseCommand
from django.db import transaction
from monitoringapp.models import User, Designation


class Command(BaseCommand):
    help = "Copy existing employee designations into department-specific choices."

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        rows = User.objects.exclude(department_id=None).values_list("department_id", "designation").distinct()
        for department_id, designation in rows:
            name = (designation or "").strip()
            if not name:
                continue
            if not Designation.objects.filter(department_id=department_id, name=name).exists():
                # Keep exact spelling so employee edit forms can select their existing value.
                match = Designation.objects.filter(department_id=department_id, name__iexact=name).first()
                if match:
                    User.objects.filter(department_id=department_id, designation=designation).update(designation=match.name)
                else:
                    Designation.objects.create(department_id=department_id, name=name)
                    created += 1
            if designation != name:
                User.objects.filter(department_id=department_id, designation=designation).update(designation=name)
        self.stdout.write(self.style.SUCCESS(f"Added {created} department designation choices."))
