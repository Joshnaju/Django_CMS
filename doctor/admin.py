from django.contrib import admin

from .models import Doctor, MedicinePrescription


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = (
        "user_profile",
        "department",
        "consultation_fee",
    )

    list_filter = ("department",)


admin.site.register(MedicinePrescription)