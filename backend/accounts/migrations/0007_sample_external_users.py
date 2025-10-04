from __future__ import annotations

from django.contrib.auth.hashers import make_password
from django.db import migrations


SAMPLE_USERS = [
    {
        "email": "anna.kowalska@pkobp.pl",
        "first_name": "Anna",
        "last_name": "Kowalska",
        "role": "entity_admin",
        "user_type": "bank",
        "phone_number": "+48 22 345 67 89",
        "password": "BezpieczneHaslo123!",
    },
    {
        "email": "piotr.nowak@santander.pl",
        "first_name": "Piotr",
        "last_name": "Nowak",
        "role": "submitter",
        "user_type": "bank",
        "phone_number": "+48 22 789 01 23",
        "password": "StabilneHaslo456@",
    },
    {
        "email": "magdalena.zielinska@pfrtfi.pl",
        "first_name": "Magdalena",
        "last_name": "Zielinska",
        "role": "entity_admin",
        "user_type": "fundusz_inwestycyjny",
        "phone_number": "+48 22 901 23 45",
        "password": "FunduszMocny789#",
    },
    {
        "email": "tomasz.maj@tfialior.pl",
        "first_name": "Tomasz",
        "last_name": "Maj",
        "role": "representative",
        "user_type": "fundusz_inwestycyjny",
        "phone_number": "+48 22 654 32 10",
        "password": "BezpiecznyFundusz321$",
    },
    {
        "email": "katarzyna.lewandowska@bgk.pl",
        "first_name": "Katarzyna",
        "last_name": "Lewandowska",
        "role": "read_only",
        "user_type": "inne",
        "phone_number": "+48 22 111 22 33",
        "password": "InneInstytucje654%",
    },
    {
        "email": "andrzej.wisniewski@pfrsa.pl",
        "first_name": "Andrzej",
        "last_name": "Wisniewski",
        "role": "submitter",
        "user_type": "inne",
        "phone_number": "+48 22 567 89 10",
        "password": "StabilnyKapital987&",
    },
]


def create_sample_users(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    for entry in SAMPLE_USERS:
        if User.objects.filter(email=entry["email"]).exists():
            continue
        User.objects.create(
            email=entry["email"],
            username=entry["email"],
            password=make_password(entry["password"]),
            first_name=entry["first_name"],
            last_name=entry["last_name"],
            role=entry["role"],
            user_type=entry["user_type"],
            phone_number=entry["phone_number"],
            preferred_language="pl",
            must_change_password=False,
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )


def remove_sample_users(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    emails = [entry["email"] for entry in SAMPLE_USERS]
    User.objects.filter(email__in=emails).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_remove_entitymembership_accounts_entitymembership_unique_and_more"),
    ]

    operations = [
        migrations.RunPython(create_sample_users, remove_sample_users),
    ]
