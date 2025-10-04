from __future__ import annotations

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_admin_password_length"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="user_type",
            field=models.CharField(
                choices=[
                    ("bank", "Bank"),
                    ("fundusz_inwestycyjny", "Fundusz inwestycyjny"),
                    ("inne", "Inne"),
                ],
                default="inne",
                max_length=64,
            ),
        ),
        migrations.CreateModel(
            name="UserGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=128, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="created_groups",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="UserGroupMembership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("added_at", models.DateTimeField(auto_now_add=True)),
                (
                    "group",
                    models.ForeignKey(on_delete=models.CASCADE, related_name="memberships", to="accounts.usergroup"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        related_name="group_memberships",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["group", "user"],
                "unique_together": {("group", "user")},
            },
        ),
        migrations.AddField(
            model_name="usergroup",
            name="users",
            field=models.ManyToManyField(
                related_name="custom_groups",
                through="accounts.UserGroupMembership",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
