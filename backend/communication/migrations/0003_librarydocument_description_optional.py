from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("communication", "0002_librarydocument_file_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="librarydocument",
            name="description",
            field=models.TextField(blank=True),
        ),
    ]
