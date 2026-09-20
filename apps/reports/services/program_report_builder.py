from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from statistics import mean

from apps.assessments.models import Assessment
from apps.programs.models import ParticipantPhase

from .report_builder import build_assessment_report


def _json_safe(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _serialize_artifacts(progress):
    return [
        {
            "name": item.original_name,
            "description": item.description,
            "uploaded_by": item.uploaded_by.email,
            "created_at": item.created_at.isoformat(),
            "size_bytes": item.size_bytes,
        }
        for item in progress.artifacts.select_related("uploaded_by").all()
    ]


def _serialize_comments(progress):
    return [
        {
            "author": item.author.email,
            "body": item.body,
            "created_at": item.created_at.isoformat(),
        }
        for item in progress.comments.select_related("author").filter(is_internal=False)
    ]


def build_individual_program_snapshot(participation):
    engagement = participation.engagement
    assessment = (
        participation.assessments.select_related("template", "participant")
        .filter(status=Assessment.Status.COMPLETED)
        .order_by("-completed_at", "-id")
        .first()
    )

    assessment_report = _json_safe(build_assessment_report(assessment)) if assessment else None
    phases = []

    for progress in (
        participation.phase_progress.select_related("phase")
        .prefetch_related(
            "artifacts__uploaded_by",
            "comments__author",
            "transformation_sessions",
            "dream_map_nodes__parent",
            "action_goals__items",
        )
        .order_by("phase__order", "id")
    ):
        phase_data = {
            "order": progress.phase.order,
            "code": progress.phase.code,
            "name": progress.phase.name,
            "status": progress.status,
            "status_label": progress.get_status_display(),
            "started_at": progress.started_at.isoformat() if progress.started_at else None,
            "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
            "notes": progress.notes,
            "artifacts": _serialize_artifacts(progress),
            "comments": _serialize_comments(progress),
        }

        if progress.phase.code == "conversaciones":
            phase_data["sessions"] = [
                {
                    "date": session.session_date.isoformat(),
                    "title": session.title,
                    "topics": session.topics,
                    "findings": session.findings,
                    "commitments": session.commitments,
                    "consultant_appreciation": session.consultant_appreciation,
                }
                for session in progress.transformation_sessions.all()
            ]
        elif progress.phase.code == "mapa-retos-suenos":
            phase_data["nodes"] = [
                {
                    "id": node.pk,
                    "type": node.node_type,
                    "type_label": node.get_node_type_display(),
                    "title": node.title,
                    "description": node.description,
                    "priority": node.priority,
                    "priority_label": node.get_priority_display(),
                    "target_date": node.target_date.isoformat() if node.target_date else None,
                    "parent_id": node.parent_id,
                    "parent_title": node.parent.title if node.parent else "",
                }
                for node in progress.dream_map_nodes.select_related("parent").all()
            ]
        elif progress.phase.code == "plan-accion":
            phase_data["goals"] = [
                {
                    "title": goal.title,
                    "description": goal.description,
                    "target_date": goal.target_date.isoformat() if goal.target_date else None,
                    "items": [
                        {
                            "action": item.action,
                            "indicator": item.indicator,
                            "responsible": item.responsible,
                            "due_date": item.due_date.isoformat() if item.due_date else None,
                            "status": item.status,
                            "status_label": item.get_status_display(),
                            "consultant_appreciation": item.consultant_appreciation,
                        }
                        for item in goal.items.all()
                    ],
                }
                for goal in progress.action_goals.prefetch_related("items").all()
            ]

        phases.append(phase_data)

    return {
        "participant": {
            "id": participation.participant_id,
            "name": participation.participant.get_full_name() or participation.participant.email,
            "email": participation.participant.email,
        },
        "engagement": {
            "id": engagement.pk,
            "title": engagement.title,
            "program": engagement.program.name,
            "organization": engagement.organization.name if engagement.organization else "",
            "consultant": engagement.consultant.email,
            "start_date": engagement.start_date.isoformat() if engagement.start_date else None,
            "end_date": engagement.end_date.isoformat() if engagement.end_date else None,
        },
        "progress_percent": participation.progress_percent,
        "assessment": {
            "id": assessment.pk,
            "template": assessment.template.name,
            "version": assessment.template.version,
            "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
            "report": assessment_report,
        } if assessment else None,
        "phases": phases,
    }


def build_organizational_program_snapshot(engagement):
    participations = list(
        engagement.participants.filter(is_active=True)
        .select_related("participant")
        .prefetch_related("assessments__template")
    )

    completed_assessments = []
    for participation in participations:
        assessment = (
            participation.assessments.select_related("template", "participant")
            .filter(status=Assessment.Status.COMPLETED)
            .order_by("-completed_at", "-id")
            .first()
        )
        if assessment:
            completed_assessments.append(assessment)

    dimension_scores = defaultdict(list)
    dimension_labels = {}

    for assessment in completed_assessments:
        report = build_assessment_report(assessment)
        for dimension in report["dimensions"]:
            if dimension["average"] is None:
                continue
            key = dimension["slug"]
            dimension_labels[key] = dimension["name"]
            dimension_scores[key].append(float(dimension["average"]))

    dimension_averages = [
        {
            "slug": slug,
            "name": dimension_labels[slug],
            "average": round(mean(scores), 2),
            "participants": len(scores),
        }
        for slug, scores in dimension_scores.items()
    ]
    dimension_averages.sort(key=lambda item: item["name"])

    phase_summary = []
    for phase in engagement.program.phases.filter(scope="PARTICIPANT").order_by("order"):
        statuses = defaultdict(int)
        for progress in ParticipantPhase.objects.filter(
            engagement_participant__engagement=engagement,
            engagement_participant__is_active=True,
            phase=phase,
        ):
            statuses[progress.status] += 1
        phase_summary.append(
            {
                "order": phase.order,
                "code": phase.code,
                "name": phase.name,
                "statuses": dict(statuses),
            }
        )

    completed_individual_reports = sum(
        1
        for participation in participations
        if participation.phase_progress.filter(
            phase__code="reporte-individual",
            status=ParticipantPhase.Status.COMPLETED,
        ).exists()
    )

    return {
        "engagement": {
            "id": engagement.pk,
            "title": engagement.title,
            "program": engagement.program.name,
            "organization": engagement.organization.name if engagement.organization else "",
            "consultant": engagement.consultant.email,
            "start_date": engagement.start_date.isoformat() if engagement.start_date else None,
            "end_date": engagement.end_date.isoformat() if engagement.end_date else None,
        },
        "participants": {
            "total": len(participations),
            "completed_assessments": len(completed_assessments),
            "completed_individual_reports": completed_individual_reports,
        },
        "dimension_averages": dimension_averages,
        "phase_summary": phase_summary,
        "privacy_note": (
            "Este reporte utiliza resultados agregados. Las respuestas abiertas "
            "individuales no se incluyen de forma identificable."
        ),
    }
