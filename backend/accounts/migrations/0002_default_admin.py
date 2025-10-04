from __future__ import annotations

from django.contrib.auth.hashers import make_password
from django.db import migrations


def create_default_admin(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    if not User.objects.filter(email="admin@example.com").exists():
        User.objects.create(
            email="admin@example.com",
            first_name="Platform",
            last_name="Administrator",
            is_staff=True,
            is_superuser=True,
            role="system_admin",
            username="admin",  # maintain backwards compatibility for legacy username field
            password=make_password("admin"),
        )


def remove_default_admin(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(email="admin@example.com").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_admin, remove_default_admin),
    ]
