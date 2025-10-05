from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("communication", "0008_remove_announcementacknowledgement_communication_announcement_ack_unique_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="librarydocument",
            name="uploaded_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name="uploaded_library_documents",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
