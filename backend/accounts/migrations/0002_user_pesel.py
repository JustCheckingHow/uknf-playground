from __future__ import annotations

from django.core.validators import RegexValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="pesel",
            field=models.CharField(
                blank=True,
                max_length=11,
                validators=[RegexValidator(r"^\d{11}$", "Niepoprawny numer PESEL")],
                help_text="Numer PESEL użytkownika przechowywany na potrzeby weryfikacji.",
            ),
        ),
    ]
