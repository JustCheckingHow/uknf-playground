from __future__ import annotations

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("communication", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="librarydocument",
            name="content",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="librarydocument",
            name="file",
            field=models.FileField(blank=True, null=True, upload_to="library/documents/"),
        ),
        migrations.AddField(
            model_name="librarydocument",
            name="uploaded_at",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="librarydocument",
            name="document_url",
            field=models.URLField(blank=True),
        ),
    ]
