from rest_framework import serializers

from .models import MedicineInventory


class MedicineInventorySerializer(serializers.ModelSerializer):

    medicine_name = serializers.CharField(
        source="medicine.name",
        read_only=True
    )

    dosage_form = serializers.CharField(
        source="medicine.dosage_form",
        read_only=True
    )

    class Meta:
        model = MedicineInventory

        fields = [
            "id",
            "medicine",
            "medicine_name",
            "dosage_form",
            "stock",
            "batch_number",
            "manufacturing_date",
            "expiry_date",
            "number_of_units",
        ]