import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("programs", "0001_initial"),
        ("assessments", "0006_ensure_open_questions_all_versions"),
    ]

    operations = [
        migrations.AddField(
            model_name="assessment",
            name="engagement_participant",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="assessments",
                to="programs.engagementparticipant",
            ),
        ),
    ]
