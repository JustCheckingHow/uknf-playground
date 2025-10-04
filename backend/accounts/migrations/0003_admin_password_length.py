from __future__ import annotations

from django.contrib.auth.hashers import make_password
from django.db import migrations


def update_admin_password(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    try:
        user = User.objects.get(email="admin@example.com")
    except User.DoesNotExist:
        return
    user.password = make_password("Admin1234!")
    user.save(update_fields=["password"])


def noop(apps, schema_editor):
    # leave password unchanged on reverse
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_default_admin"),
    ]

    operations = [
        migrations.RunPython(update_admin_password, noop),
    ]
