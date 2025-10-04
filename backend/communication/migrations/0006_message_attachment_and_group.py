from __future__ import annotations

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_user_groups"),
        ("communication", "0005_messagethread_global"),
    ]

    operations = [
        migrations.AddField(
            model_name="messagethread",
            name="target_group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name="message_threads",
                to="accounts.usergroup",
            ),
        ),
        migrations.AddField(
            model_name="message",
            name="attachment",
            field=models.FileField(blank=True, null=True, upload_to="communication/messages/"),
        ),
        migrations.AddField(
            model_name="message",
            name="recipient",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name="received_messages",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RemoveField(
            model_name="message",
            name="attachments",
        ),
    ]
