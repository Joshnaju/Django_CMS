from django import forms
from django.contrib.auth.models import User

from .models import UserProfile
from departments.models import Department


class CustomUserCreationForm(forms.ModelForm):

    name = forms.CharField(
        max_length=150,
        required=True,
        label="Name"
    )

    email = forms.EmailField(
        required=True,
        label="Email"
    )

    password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        label="Password"
    )

    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        required=True,
        label="Role"
    )

    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        label="Department"
    )

    consultation_fee = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label="Consultation Fee"
    )

    class Meta:
        model = User
        fields = (
            "name",
            "email",
            "password",
        )

    def clean(self):

        cleaned_data = super().clean()

        role = cleaned_data.get("role")


        department = cleaned_data.get("department")
        consultation_fee = cleaned_data.get("consultation_fee")

        if role == "DOCTOR":

            if not department:
                self.add_error(
                    "department",
                    "Department is required for Doctor."
                )

            if consultation_fee is None:
                self.add_error(
                    "consultation_fee",
                    "Consultation fee is required for Doctor."
                )

        return cleaned_data

    def save(self, commit=True):

        user = super().save(commit=False)

        name = self.cleaned_data["name"]
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password"]

        # Generate username
        parts = name.strip().split()
        base_name = parts[0]

        role = self.cleaned_data["role"]

        role_codes = {
            "ADMIN": "ADM",
            "RECEPTIONIST": "REC",
            "DOCTOR": "DOC",
            "PHARMACIST": "PHA",
            "LAB_TECHNICIAN": "LAB",
        }

        role_code = role_codes[role]

        # Count existing users with this role code
        number = User.objects.filter(
            username__regex=rf"@{role_code}[0-9]+$"
        ).count() + 1

        username = f"{base_name}@{role_code}{number}"

        # Safety check in case a username already exists
        while User.objects.filter(username=username).exists():
            number += 1
            username = f"{base_name}@{role_code}{number}"

        user.username = username
        user.email = email
        user.set_password(password)

        if commit:
            user.save()

        return user