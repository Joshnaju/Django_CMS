from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm
from .models import UserProfile

from doctor.models import Doctor


admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    add_form = CustomUserCreationForm

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "name",
                    "email",
                    "password",
                    "role",
                    "department",
                    "consultation_fee",
                ),
            },
        ),
    )

    class Media:
        js = (
            "accounts/js/user_form.js",
        )

    def save_model(self, request, obj, form, change):

        # Save User first
        super().save_model(request, obj, form, change)

        # Only create profile when adding a new user
        if not change:

            profile = UserProfile.objects.create(
                user=obj,
                name=form.cleaned_data["name"],
                role=form.cleaned_data["role"],
            )

            # Create Doctor record only for Doctor role
            if form.cleaned_data["role"] == "DOCTOR":

                Doctor.objects.create(
                    user_profile=profile,
                    department=form.cleaned_data["department"],
                    consultation_fee=form.cleaned_data["consultation_fee"],
                )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "name",
        "role",
    )

    list_filter = (
        "role",
    )

    search_fields = (
        "name",
        "user__username",
        "user__email",
    )