from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "nombre@correo.com",
                "class": "form-control",
            }
        ),
    )

    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "placeholder": "Ingresa tu contraseña",
                "class": "form-control",
            }
        ),
    )

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)

        from allauth.account.models import EmailAddress

        email_record = EmailAddress.objects.filter(user=user, email__iexact=user.email).first()
        if email_record is not None and not email_record.verified:
            raise forms.ValidationError(
                "Confirma tu correo electrónico antes de iniciar sesión.",
                code="email_not_verified",
            )


class PublicSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].label = "Correo electrónico"
        self.fields["email"].widget.attrs.update(
            {
                "class": "form-control",
                "autocomplete": "email",
                "placeholder": "nombre@correo.com",
            }
        )
        self.fields["password1"].label = "Contraseña"
        self.fields["password1"].widget.attrs.update(
            {
                "class": "form-control",
                "autocomplete": "new-password",
            }
        )
        self.fields["password2"].label = "Confirmar contraseña"
        self.fields["password2"].widget.attrs.update(
            {
                "class": "form-control",
                "autocomplete": "new-password",
            }
        )


class UserCreateForm(UserCreationForm):
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "persona@correo.com",
                "class": "form-control",
            }
        ),
    )
    role = forms.ChoiceField(
        label="Rol",
        choices=(
            (User.Role.ADMIN, "Administrador"),
            (User.Role.USER, "Usuario"),
        ),
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    password1 = forms.CharField(
        label="Contraseña temporal",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "class": "form-control",
            }
        ),
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "class": "form-control",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("email", "role")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo electrónico.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.role = self.cleaned_data["role"]
        user.is_staff = user.role == User.Role.ADMIN
        user.is_superuser = False
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "class": "form-control",
            }
        ),
    )
    role = forms.ChoiceField(
        label="Rol",
        choices=(
            (User.Role.ADMIN, "Administrador"),
            (User.Role.USER, "Usuario"),
        ),
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = User
        fields = ("email", "role")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        duplicate = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo electrónico.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = user.role == User.Role.ADMIN
        user.is_superuser = False
        if commit:
            user.save()
        return user
