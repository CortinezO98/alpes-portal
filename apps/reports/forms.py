from django import forms

from apps.accounts.models import User
from apps.assessments.models import Assessment


class AnalyticsFilterForm(forms.Form):
    status = forms.ChoiceField(
        label="Estado",
        required=False,
        choices=(("", "Todos los estados"), *Assessment.Status.choices),
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    participant = forms.ModelChoiceField(
        label="Participante",
        required=False,
        queryset=User.objects.none(),
        empty_label="Todos los participantes",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    date_from = forms.DateField(
        label="Desde",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    date_to = forms.DateField(
        label="Hasta",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["participant"].queryset = User.objects.filter(
            role=User.Role.USER,
        ).order_by("email")

    def clean(self):
        cleaned = super().clean()
        date_from = cleaned.get("date_from")
        date_to = cleaned.get("date_to")
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("La fecha inicial no puede ser posterior a la fecha final.")
        return cleaned


from .models import DimensionAppreciation, IndividualReportVersion, OrganizationalReportVersion


class DimensionAppreciationForm(forms.ModelForm):
    class Meta:
        model = DimensionAppreciation
        fields = ("interpretation", "strengths", "opportunities", "recommendation")
        widgets = {
            "interpretation": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Lectura profesional de esta dimensión...",
                }
            ),
            "strengths": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Fortalezas identificadas...",
                }
            ),
            "opportunities": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Oportunidades de mejora...",
                }
            ),
            "recommendation": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Recomendación o siguiente acción...",
                }
            ),
        }
        labels = {
            "interpretation": "Lectura profesional",
            "strengths": "Fortalezas identificadas",
            "opportunities": "Oportunidades",
            "recommendation": "Recomendación",
        }



class IndividualReportVersionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in (
            "executive_summary",
            "integral_appreciation",
            "recommendations",
            "conclusions",
        ):
            self.fields[name].required = True

    class Meta:
        model = IndividualReportVersion
        fields = (
            "executive_summary",
            "integral_appreciation",
            "recommendations",
            "conclusions",
        )
        widgets = {
            "executive_summary": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "placeholder": "Resumen ejecutivo del proceso..."}
            ),
            "integral_appreciation": forms.Textarea(
                attrs={"class": "form-control", "rows": 5, "placeholder": "Lectura integral del acompañamiento..."}
            ),
            "recommendations": forms.Textarea(
                attrs={"class": "form-control", "rows": 5, "placeholder": "Recomendaciones profesionales..."}
            ),
            "conclusions": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "placeholder": "Conclusiones del proceso..."}
            ),
        }
        labels = {
            "executive_summary": "Resumen ejecutivo",
            "integral_appreciation": "Apreciación integral",
            "recommendations": "Recomendaciones",
            "conclusions": "Conclusiones",
        }


class OrganizationalReportVersionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in (
            "executive_summary",
            "organizational_appreciation",
            "recommendations",
            "conclusions",
        ):
            self.fields[name].required = True

    class Meta:
        model = OrganizationalReportVersion
        fields = (
            "executive_summary",
            "organizational_appreciation",
            "recommendations",
            "conclusions",
        )
        widgets = {
            "executive_summary": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "placeholder": "Resumen ejecutivo del acompañamiento organizacional..."}
            ),
            "organizational_appreciation": forms.Textarea(
                attrs={"class": "form-control", "rows": 5, "placeholder": "Lectura profesional de los resultados agregados..."}
            ),
            "recommendations": forms.Textarea(
                attrs={"class": "form-control", "rows": 5, "placeholder": "Recomendaciones para la organización..."}
            ),
            "conclusions": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "placeholder": "Conclusiones organizacionales..."}
            ),
        }
        labels = {
            "executive_summary": "Resumen ejecutivo",
            "organizational_appreciation": "Apreciación organizacional",
            "recommendations": "Recomendaciones",
            "conclusions": "Conclusiones",
        }
