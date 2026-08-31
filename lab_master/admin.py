from django.contrib import admin
from .models import LabTest

@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "normal_range",
        "unit",
        "price",
        "is_active",
    )

    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("name",)
