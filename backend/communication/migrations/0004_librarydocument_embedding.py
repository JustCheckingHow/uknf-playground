from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("communication", "0003_librarydocument_description_optional"),
    ]

    operations = [
        migrations.AddField(
            model_name="librarydocument",
            name="embedding",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
