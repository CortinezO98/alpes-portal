from statistics import mean

from apps.assessments.models import Answer, Question

from apps.reports.models import DimensionAppreciation

from .scoring import get_score_band


def build_assessment_report(assessment):
    answers = list(
        Answer.objects.filter(assessment=assessment)
        .select_related("question", "question__dimension")
        .order_by("question__order", "question__id")
    )
    answers_by_question = {answer.question_id: answer for answer in answers}

    appreciations = {
        item.dimension_id: item
        for item in DimensionAppreciation.objects.filter(
            assessment=assessment
        ).select_related("dimension", "consultant")
    }

    dimensions = []
    for dimension in assessment.template.dimensions.prefetch_related("questions").order_by("order", "id"):
        question_rows = []
        scores = []

        for question in dimension.questions.all().order_by("order", "id"):
            answer = answers_by_question.get(question.pk)
            if question.question_type != Question.Type.SCALE:
                continue

            score = answer.score if answer else None
            if score is not None:
                scores.append(float(score))
            band = get_score_band(score) if score is not None else None

            question_rows.append(
                {
                    "id": question.pk,
                    "order": question.order,
                    "text": question.text,
                    "score": score,
                    "band": band.code if band else "neutral",
                    "band_label": band.label if band else "Sin respuesta",
                    "band_color": band.color if band else "#A7B0AA",
                    "percentage": float(score or 0) * 10,
                }
            )

        average = round(mean(scores), 2) if scores else None
        band = get_score_band(average) if average is not None else None
        appreciation = appreciations.get(dimension.pk)
        dimensions.append(
            {
                "id": dimension.pk,
                "slug": dimension.slug,
                "order": dimension.order,
                "name": dimension.name,
                "description": dimension.description,
                "average": average,
                "band": band.code if band else "neutral",
                "band_label": band.label if band else "Sin resultado",
                "band_color": band.color if band else "#A7B0AA",
                "questions": question_rows,
                "appreciation": {
                    "interpretation": appreciation.interpretation if appreciation else "",
                    "strengths": appreciation.strengths if appreciation else "",
                    "opportunities": appreciation.opportunities if appreciation else "",
                    "recommendation": appreciation.recommendation if appreciation else "",
                    "consultant": appreciation.consultant.email if appreciation else "",
                    "updated_at": appreciation.updated_at if appreciation else None,
                },
            }
        )

    general_answers = []
    for question in assessment.template.general_questions.order_by("order", "id"):
        answer = answers_by_question.get(question.pk)
        general_answers.append(
            {
                "id": question.pk,
                "order": question.order,
                "question": question.text,
                "answer": answer.text.strip() if answer and answer.text else "",
            }
        )

    return {
        "dimensions": dimensions,
        "general_answers": general_answers,
        "radar": [
            {
                "label": dimension["name"],
                "score": dimension["average"] or 0,
                "band": dimension["band"],
                "band_label": dimension["band_label"],
                "color": dimension["band_color"],
            }
            for dimension in dimensions
        ],
    }
