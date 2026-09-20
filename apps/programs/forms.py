from django import forms

from apps.accounts.models import User

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
