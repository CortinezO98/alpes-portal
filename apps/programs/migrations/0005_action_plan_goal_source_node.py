from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("programs", "0004_consultant_experience_record"),
    ]

    operations = [
        migrations.AddField(
            model_name="actionplangoal",
            name="source_node",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="linked_action_goals",
                to="programs.dreamchallengenode",
            ),
        ),
    ]
