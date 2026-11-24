from django.db import migrations


def seed_branches(apps, schema_editor):
    Branch = apps.get_model("monitoringapp", "Branch")
    Branch.objects.get_or_create(
        name="Kochi",
        defaults={"code": "KOC", "is_head_office": True, "is_active": True},
    )
    Branch.objects.get_or_create(
        name="Coimbatore",
        defaults={"code": "CBE", "is_head_office": False, "is_active": True},
    )


class Migration(migrations.Migration):

    dependencies = [
        ("monitoringapp", "0044_add_branch"),
    ]

    operations = [
        migrations.RunPython(seed_branches, migrations.RunPython.noop),
    ]