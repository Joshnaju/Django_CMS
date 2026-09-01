from rest_framework import serializers

from .models import MedicineInventory


class MedicineInventorySerializer(serializers.ModelSerializer):

    medicine_name = serializers.CharField(
        source="medicine.name",
        read_only=True
    )

    generic_name = serializers.CharField(
        source="medicine.generic_name",
        read_only=True
    )

    dosage_form = serializers.CharField(
        source="medicine.dosage_form",
        read_only=True
    )

    strength = serializers.CharField(
        source="medicine.strength",
        read_only=True
    )

    manufacturer = serializers.CharField(
        source="medicine.manufacturer",
        read_only=True
    )

    price = serializers.DecimalField(
        source="medicine.price",
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = MedicineInventory

        fields = [
            "id",

            # Medicine Master details
            "medicine",
            "medicine_name",
            "generic_name",
            "dosage_form",
            "strength",
            "manufacturer",
            "price",

            # Pharmacy details
            "stock",
            "batch_number",
            "manufacturing_date",
            "expiry_date",
            "number_of_units",
        ]