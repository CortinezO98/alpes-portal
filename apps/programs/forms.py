from django import forms

from apps.accounts.models import User
from apps.assessments.models import AssessmentTemplate

from .models import Engagement, EngagementParticipant, Organization, ServiceProgram


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = (
            "name", "tax_id", "contact_name", "contact_email",
            "contact_phone", "city", "notes",
        )
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "tax_id": forms.TextInput(attrs={"class": "form-control"}),
            "contact_name": forms.TextInput(attrs={"class": "form-control"}),
            "contact_email": forms.EmailInput(attrs={"class": "form-control"}),
            "contact_phone": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class EngagementForm(forms.ModelForm):
    class Meta:
        model = Engagement
        fields = (
            "title", "program", "mode", "organization", "status",
            "start_date", "end_date", "notes",
        )
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "program": forms.Select(attrs={"class": "form-control"}),
            "mode": forms.Select(attrs={"class": "form-control"}),
            "organization": forms.Select(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        labels = {
            "title": "Nombre del proceso",
            "program": "Programa",
            "mode": "Modalidad",
            "organization": "Organización",
            "status": "Estado",
            "start_date": "Fecha de inicio",
            "end_date": "Fecha de cierre",
            "notes": "Notas",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["program"].queryset = ServiceProgram.objects.filter(is_active=True).order_by("name")
        self.fields["organization"].required = False
        self.fields["organization"].queryset = Organization.objects.filter(is_active=True).order_by("name")

    def clean(self):
        cleaned = super().clean()
        mode = cleaned.get("mode")
        organization = cleaned.get("organization")
        start_date = cleaned.get("start_date")
        end_date = cleaned.get("end_date")
        if mode == Engagement.Mode.ORGANIZATIONAL and not organization:
            self.add_error("organization", "Selecciona una organización.")
        if mode == Engagement.Mode.INDIVIDUAL:
            cleaned["organization"] = None
        if start_date and end_date and end_date < start_date:
            self.add_error("end_date", "La fecha de cierre no puede ser anterior al inicio.")
        return cleaned


class EngagementParticipantForm(forms.ModelForm):
    class Meta:
        model = EngagementParticipant
        fields = ("participant",)
        widgets = {"participant": forms.Select(attrs={"class": "form-control"})}
        labels = {"participant": "Participante"}

    def __init__(self, *args, engagement, **kwargs):
        super().__init__(*args, **kwargs)
        self.engagement = engagement
        current_ids = engagement.participants.values_list("participant_id", flat=True)
        self.fields["participant"].queryset = User.objects.filter(
            role=User.Role.USER,
            is_active=True,
        ).exclude(pk__in=current_ids).order_by("email")

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.engagement = self.engagement
        if commit:
            obj.save()
        return obj


class UnifiedEngagementCreateForm(forms.Form):
    mode = forms.ChoiceField(
        label="Tipo de acompañamiento",
        choices=Engagement.Mode.choices,
        initial=Engagement.Mode.ORGANIZATIONAL,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )
    title = forms.CharField(
        label="Nombre del proceso",
        max_length=200,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ej. Jubilación Plena · Ecopetrol 2026",
            }
        ),
    )
    program = forms.ModelChoiceField(
        label="Programa",
        queryset=ServiceProgram.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    organization = forms.ModelChoiceField(
        label="Empresa / organización",
        queryset=Organization.objects.none(),
        required=False,
        empty_label="Selecciona una organización existente",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    create_organization = forms.BooleanField(
        label="Crear una empresa nueva en este mismo formulario",
        required=False,
        widget=forms.HiddenInput(),
    )
    organization_name = forms.CharField(
        label="Nombre de la empresa",
        max_length=180,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre o razón social"}),
    )
    organization_tax_id = forms.CharField(
        label="NIT",
        max_length=40,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "NIT / identificación tributaria"}),
    )
    organization_contact_name = forms.CharField(
        label="Contacto",
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Persona de contacto"}),
    )
    organization_contact_email = forms.EmailField(
        label="Correo de contacto",
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "contacto@empresa.com"}),
    )
    participants = forms.ModelMultipleChoiceField(
        label="Participantes existentes",
        queryset=User.objects.none(),
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-select",
                "size": 7,
                "data-participant-selector": "true",
            }
        ),
    )
    new_participants_json = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "id_new_participants_json"}),
    )
    status = forms.ChoiceField(
        label="Estado inicial",
        choices=Engagement.Status.choices,
        initial=Engagement.Status.ACTIVE,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    start_date = forms.DateField(
        label="Fecha de inicio",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    end_date = forms.DateField(
        label="Fecha estimada de cierre",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    assign_assessment = forms.BooleanField(
        label="Asignar automáticamente la evaluación de Jubilación Plena",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    assessment_template = forms.ModelChoiceField(
        label="Plantilla de evaluación",
        queryset=AssessmentTemplate.objects.none(),
        required=False,
        empty_label="Selecciona una plantilla",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    notes = forms.CharField(
        label="Notas internas",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Información adicional para el equipo de acompañamiento.",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["program"].queryset = ServiceProgram.objects.filter(
            is_active=True
        ).order_by("name")
        self.fields["organization"].queryset = Organization.objects.filter(
            is_active=True
        ).order_by("name")
        self.fields["participants"].queryset = User.objects.filter(
            role=User.Role.USER,
            is_active=True,
        ).order_by("first_name", "last_name", "email")
        templates = AssessmentTemplate.objects.filter(
            is_active=True,
            publication_status=AssessmentTemplate.PublicationStatus.PUBLISHED,
        ).order_by("name", "-version")
        self.fields["assessment_template"].queryset = templates

        retirement_program = self.fields["program"].queryset.filter(
            code="jubilacion-plena"
        ).first()
        if retirement_program:
            self.fields["program"].initial = retirement_program

        retirement_template = templates.filter(
            slug__startswith="alpes-jubilacion-plena"
        ).first()
        if retirement_template:
            self.fields["assessment_template"].initial = retirement_template

    def clean_new_participants_json(self):
        import json

        raw = self.cleaned_data.get("new_participants_json", "")
        if not raw:
            return []
        try:
            rows = json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError):
            raise forms.ValidationError("No fue posible leer los participantes nuevos.")

        if not isinstance(rows, list):
            raise forms.ValidationError("El formato de participantes nuevos no es válido.")

        normalized = []
        seen = set()
        for index, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                continue
            email = str(row.get("email", "")).strip().lower()
            first_name = str(row.get("first_name", "")).strip()
            last_name = str(row.get("last_name", "")).strip()
            password = str(row.get("password", ""))

            if not email and not first_name and not last_name and not password:
                continue
            if not email:
                raise forms.ValidationError(
                    f"Falta el correo del participante nuevo #{index}."
                )
            if "@" not in email:
                raise forms.ValidationError(
                    f"El correo del participante nuevo #{index} no es válido."
                )
            if email in seen:
                raise forms.ValidationError(
                    f"El correo {email} está repetido entre los participantes nuevos."
                )
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError(
                    f"{email} ya existe. Selecciónalo en participantes existentes."
                )
            if len(password) < 8:
                raise forms.ValidationError(
                    f"La contraseña temporal de {email} debe tener al menos 8 caracteres."
                )
            seen.add(email)
            normalized.append(
                {
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "password": password,
                }
            )
        return normalized

    def clean(self):
        cleaned = super().clean()
        mode = cleaned.get("mode")
        organization = cleaned.get("organization")
        create_organization = cleaned.get("create_organization")
        organization_name = (cleaned.get("organization_name") or "").strip()
        selected_participants = cleaned.get("participants")
        new_participants = cleaned.get("new_participants_json") or []
        assign_assessment = cleaned.get("assign_assessment")
        assessment_template = cleaned.get("assessment_template")
        start_date = cleaned.get("start_date")
        end_date = cleaned.get("end_date")

        if mode == Engagement.Mode.ORGANIZATIONAL:
            if create_organization:
                if not organization_name:
                    self.add_error(
                        "organization_name",
                        "Escribe el nombre de la empresa que deseas crear.",
                    )
                cleaned["organization"] = None
            elif not organization:
                self.add_error(
                    "organization",
                    "Selecciona una empresa existente o crea una nueva aquí mismo.",
                )
        else:
            cleaned["organization"] = None
            cleaned["create_organization"] = False

        selected_count = len(selected_participants) if selected_participants is not None else 0
        total_participants = selected_count + len(new_participants)
        if total_participants == 0:
            self.add_error(
                "participants",
                "Selecciona o crea al menos un participante.",
            )
        if mode == Engagement.Mode.INDIVIDUAL and total_participants > 1:
            self.add_error(
                "participants",
                "Un acompañamiento individual debe tener un solo participante.",
            )

        if assign_assessment and not assessment_template:
            self.add_error(
                "assessment_template",
                "Selecciona la plantilla que se asignará automáticamente.",
            )

        if start_date and end_date and end_date < start_date:
            self.add_error(
                "end_date",
                "La fecha estimada de cierre no puede ser anterior al inicio.",
            )
        return cleaned
