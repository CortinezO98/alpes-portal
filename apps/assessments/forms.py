from django import forms

from apps.accounts.models import User

from .models import Answer, Assessment, AssessmentTemplate, Question


class AssessmentAssignForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = ("template", "participant")
        widgets = {
            "template": forms.Select(attrs={"class": "form-control"}),
            "participant": forms.Select(attrs={"class": "form-control"}),
        }
        labels = {
            "template": "Plantilla",
            "participant": "Participante",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["template"].queryset = AssessmentTemplate.objects.filter(
            is_active=True
        ).order_by("name")
        self.fields["participant"].queryset = User.objects.filter(
            role=User.Role.USER,
            is_active=True,
        ).order_by("email")

    def clean(self):
        cleaned = super().clean()
        template = cleaned.get("template")
        participant = cleaned.get("participant")
        if template and participant:
            already_open = Assessment.objects.filter(
                template=template,
                participant=participant,
                status__in=(
                    Assessment.Status.DRAFT,
                    Assessment.Status.IN_PROGRESS,
                ),
            ).exists()
            if already_open:
                raise forms.ValidationError(
                    "El participante ya tiene una evaluación pendiente de esta plantilla."
                )
        return cleaned


class DimensionAnswerForm(forms.Form):
    def __init__(self, *args, assessment, dimension, **kwargs):
        super().__init__(*args, **kwargs)
        self.assessment = assessment
        self.dimension = dimension
        existing = {
            answer.question_id: answer.score
            for answer in assessment.answers.filter(
                question__dimension=dimension
            )
        }
        choices = [(value, str(value)) for value in range(1, 11)]

        for question in dimension.questions.filter(
            question_type=Question.Type.SCALE
        ).order_by("order", "id"):
            self.fields[f"question_{question.pk}"] = forms.TypedChoiceField(
                label=question.text,
                choices=choices,
                coerce=int,
                required=question.is_required,
                initial=existing.get(question.pk),
                widget=forms.RadioSelect(attrs={"class": "scale-input"}),
            )

    def save(self):
        for field_name, score in self.cleaned_data.items():
            question_id = int(field_name.removeprefix("question_"))
            Answer.objects.update_or_create(
                assessment=self.assessment,
                question_id=question_id,
                defaults={"score": score, "text": ""},
            )


class GeneralQuestionsForm(forms.Form):
    def __init__(self, *args, assessment, **kwargs):
        super().__init__(*args, **kwargs)
        self.assessment = assessment
        existing = {
            answer.question_id: answer.text
            for answer in assessment.answers.filter(
                question__template=assessment.template,
                question__dimension__isnull=True,
            )
        }

        for question in assessment.template.general_questions.order_by("order", "id"):
            self.fields[f"question_{question.pk}"] = forms.CharField(
                label=question.text,
                required=question.is_required,
                initial=existing.get(question.pk, ""),
                widget=forms.Textarea(
                    attrs={
                        "class": "form-control assessment-textarea",
                        "rows": 4,
                        "placeholder": "Escribe tu respuesta aquí...",
                    }
                ),
            )

    def save(self):
        for field_name, text in self.cleaned_data.items():
            question_id = int(field_name.removeprefix("question_"))
            Answer.objects.update_or_create(
                assessment=self.assessment,
                question_id=question_id,
                defaults={"score": None, "text": text.strip()},
            )
