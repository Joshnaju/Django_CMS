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
            "medicine",
            "medicine_name",
            "generic_name",
            "dosage_form",
            "strength",
            "manufacturer",
            "price",
            "stock",
            "batch_number",
            "manufacturing_date",
            "expiry_date",
            "number_of_units",
        ]

        read_only_fields = [
            "medicine"
        ]


    # Stock validation
    def validate_stock(self, value):

        if value < 0:
            raise serializers.ValidationError(
                "Stock cannot be negative."
            )

        return value


    # Number of units validation
    def validate_number_of_units(self, value):

        if value <= 0:
            raise serializers.ValidationError(
                "Number of units must be greater than zero."
            )

        return value


    # Date validation
    def validate(self, data):

        manufacturing_date = data.get(
            "manufacturing_date"
        )

        expiry_date = data.get(
            "expiry_date"
        )

        # For PATCH/PUT of existing inventory,
        # use existing values when a date is not sent.
        if self.instance:

            if manufacturing_date is None:
                manufacturing_date = (
                    self.instance.manufacturing_date
                )

            if expiry_date is None:
                expiry_date = (
                    self.instance.expiry_date
                )

        if (
            manufacturing_date
            and expiry_date
            and expiry_date <= manufacturing_date
        ):

            raise serializers.ValidationError({
                "expiry_date":
                "Expiry date must be after manufacturing date."
            })

        return data