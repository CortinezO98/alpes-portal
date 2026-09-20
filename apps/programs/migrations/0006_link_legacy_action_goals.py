from django.db import migrations


def link_legacy_goals_to_map_nodes(apps, schema_editor):
    ActionPlanGoal = apps.get_model("programs", "ActionPlanGoal")
    DreamChallengeNode = apps.get_model("programs", "DreamChallengeNode")

    for goal in ActionPlanGoal.objects.filter(source_node__isnull=True).select_related(
        "participant_phase__engagement_participant"
    ):
        participant_id = goal.participant_phase.engagement_participant_id
        matches = list(
            DreamChallengeNode.objects.filter(
                participant_phase__engagement_participant_id=participant_id,
                title=goal.title,
                description=goal.description,
                target_date=goal.target_date,
            ).values_list("pk", flat=True)[:2]
        )
        if len(matches) == 1:
            goal.source_node_id = matches[0]
            goal.save(update_fields=("source_node",))


class Migration(migrations.Migration):

    dependencies = [
        ("programs", "0005_action_plan_goal_source_node"),
    ]

    operations = [
        migrations.RunPython(
            link_legacy_goals_to_map_nodes,
            migrations.RunPython.noop,
        ),
    ]
