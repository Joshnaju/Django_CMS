from django import forms
from django.contrib import admin

from .models import Medicine


class MedicineAdminForm(forms.ModelForm):

    strength = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False
    )

    class Meta:
        model = Medicine
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()

        dosage_form = cleaned_data.get("dosage_form")
        strength = cleaned_data.get("strength")
        strength_unit = cleaned_data.get("strength_unit")

        # Powder → strength and unit are optional
        if dosage_form == "POWDER":
            return cleaned_data

        # All other dosage forms → both are required
        if not strength:
            self.add_error(
                "strength",
                "Strength is required for this dosage form."
            )

        if not strength_unit:
            self.add_error(
                "strength_unit",
                "Strength unit is required for this dosage form."
            )

        return cleaned_data

    class Media:
        js = ("admin/js/medicine_form.js",)


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):

    form = MedicineAdminForm

    list_display = (
        "name",
        "generic_name",
        "dosage_form",
        "strength",
        "strength_unit",
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