from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("communication", "0004_librarydocument_embedding"),
    ]

    operations = [
        migrations.AddField(
            model_name="messagethread",
            name="is_global",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="messagethread",
            name="entity",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.CASCADE,
                related_name="message_threads",
                to="accounts.regulatedentity",
            ),
        ),
    ]

