from django.contrib import admin
from .models import Medicine


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "generic_name",
        "dosage_form",
        "strength",
        "manufacturer",
        "price",
        "is_active",
    )

    list_filter = (
        "dosage_form",
        "is_active",
    )

    search_fields = (
        "name",
        "generic_name",
        "manufacturer",
    )

    ordering = ("name",)
