from django import forms
from django.utils.text import slugify

from apps.accounts.models import User

from .models import Answer, Assessment, AssessmentTemplate, Dimension, Question


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
            is_active=True,
            publication_status=AssessmentTemplate.PublicationStatus.PUBLISHED,
        ).order_by("name", "-version")
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


class DimensionConfigForm(forms.ModelForm):
    class Meta:
        model = Dimension
        fields = ("name", "description", "order")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
        }
        labels = {
            "name": "Nombre de la dimensión",
            "description": "Descripción",
            "order": "Orden",
        }

    def __init__(self, *args, template, **kwargs):
        super().__init__(*args, **kwargs)
        self.template = template

    def clean(self):
        cleaned = super().clean()
        name = cleaned.get("name")
        order = cleaned.get("order")
        if name:
            candidate_slug = slugify(name)
            duplicate_slug = Dimension.objects.filter(
                template=self.template,
                slug=candidate_slug,
            ).exclude(pk=self.instance.pk)
            if duplicate_slug.exists():
                self.add_error("name", "Ya existe una dimensión con este nombre.")
        if order:
            duplicate_order = Dimension.objects.filter(
                template=self.template,
                order=order,
            ).exclude(pk=self.instance.pk)
            if duplicate_order.exists():
                self.add_error("order", "Ya existe una dimensión con este orden.")
        return cleaned

    def save(self, commit=True):
        dimension = super().save(commit=False)
        dimension.template = self.template
        if not dimension.slug or "name" in self.changed_data:
            dimension.slug = slugify(dimension.name)
        if commit:
            dimension.save()
        return dimension


class ScaleQuestionConfigForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ("text", "order", "is_required")
        widgets = {
            "text": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "is_required": forms.CheckboxInput(),
        }
        labels = {
            "text": "Pregunta / ítem",
            "order": "Orden",
            "is_required": "Respuesta obligatoria",
        }

    def __init__(self, *args, dimension, **kwargs):
        super().__init__(*args, **kwargs)
        self.dimension = dimension

    def clean_order(self):
        order = self.cleaned_data["order"]
        duplicate = Question.objects.filter(
            dimension=self.dimension,
            order=order,
        ).exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise forms.ValidationError("Ya existe una pregunta con este orden.")
        return order

    def save(self, commit=True):
        question = super().save(commit=False)
        question.dimension = self.dimension
        question.template = None
        question.question_type = Question.Type.SCALE
        if commit:
            question.save()
        return question


class GeneralQuestionConfigForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ("text", "order", "is_required")
        widgets = {
            "text": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "is_required": forms.CheckboxInput(),
        }
        labels = {
            "text": "Pregunta abierta",
            "order": "Orden",
            "is_required": "Respuesta obligatoria",
        }

    def __init__(self, *args, template, **kwargs):
        super().__init__(*args, **kwargs)
        self.template = template

    def clean_order(self):
        order = self.cleaned_data["order"]
        duplicate = Question.objects.filter(
            template=self.template,
            dimension__isnull=True,
            order=order,
        ).exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise forms.ValidationError("Ya existe una pregunta abierta con este orden.")
        return order

    def save(self, commit=True):
        question = super().save(commit=False)
        question.template = self.template
        question.dimension = None
        question.question_type = Question.Type.TEXT
        if commit:
            question.save()
        return question


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
