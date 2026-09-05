from rest_framework import serializers
from .models import (MedicineInventory,PharmacyBill,PharmacyBillItem)
from doctor.models import MedicinePrescription


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

            "min_stock",
            "max_stock",

            "batch_number",
            "manufacturing_date",
            "expiry_date",
            "number_of_units",
        ]


    # ---------------- STOCK VALIDATION ----------------

    def validate_stock(self, value):

        if value < 0:

            raise serializers.ValidationError(
                "Stock cannot be negative."
            )

        return value

    # ---------------- MIN STOCK VALIDATION ----------------

    def validate_min_stock(self, value):

        if value < 0:

            raise serializers.ValidationError(
                "Minimum stock cannot be negative."
            )

        return value

    # ---------------- MAX STOCK VALIDATION ----------------

    def validate_max_stock(self, value):

        if value < 0:

            raise serializers.ValidationError(
                "Maximum stock cannot be negative."
            )

        return value

    # ---------------- NUMBER OF UNITS VALIDATION ----------------

    def validate_number_of_units(self, value):

        if value <= 0:

            raise serializers.ValidationError(
                "Number of units must be greater than zero."
            )

        return value

    # ---------------- DATE AND STOCK VALIDATION ----------------

    def validate(self, data):

        manufacturing_date = data.get(
            "manufacturing_date"
        )

        expiry_date = data.get(
            "expiry_date"
        )

        min_stock = data.get(
            "min_stock"
        )

        max_stock = data.get(
            "max_stock"
        )

        # ---------------- PATCH / PUT ----------------

        if self.instance:

            if manufacturing_date is None:

                manufacturing_date = (
                    self.instance.manufacturing_date
                )

            if expiry_date is None:

                expiry_date = (
                    self.instance.expiry_date
                )

            if min_stock is None:

                min_stock = (
                    self.instance.min_stock
                )

            if max_stock is None:

                max_stock = (
                    self.instance.max_stock
                )

        # ---------------- DATE VALIDATION ----------------

        if (
            manufacturing_date
            and expiry_date
            and expiry_date <= manufacturing_date
        ):

            raise serializers.ValidationError({

                "expiry_date":
                "Expiry date must be after manufacturing date."

            })

        # ---------------- MIN/MAX STOCK VALIDATION ----------------

        if (
            min_stock is not None
            and max_stock is not None
            and min_stock > max_stock
        ):

            raise serializers.ValidationError({

                "max_stock":
                "Maximum stock must be greater than or equal to minimum stock."

            })

        return data

class PharmacistPrescriptionSerializer(serializers.ModelSerializer):

    # ---------------- PATIENT DETAILS ----------------

    patient_id = serializers.CharField(
        source="consultation.appointment.patient.patient_id",
        read_only=True
    )

    patient_name = serializers.CharField(
        source="consultation.appointment.patient.patient_name",
        read_only=True
    )

    # ---------------- DOCTOR DETAILS ----------------

    doctor_name = serializers.CharField(
        source="consultation.appointment.doctor.user_profile.name",
        read_only=True
    )

    # ---------------- MEDICINE DETAILS ----------------

    medicine_name = serializers.SerializerMethodField()

    medicine_strength = serializers.CharField(
        source="medicine.strength",
        read_only=True,
        allow_null=True,
        default=None
    )

    medicine_strength_unit = serializers.CharField(
        source="medicine.strength_unit",
        read_only=True,
        allow_null=True,
        default=None
    )

    medicine_dosage_form = serializers.CharField(
        source="medicine.dosage_form",
        read_only=True,
        allow_null=True,
        default=None
    )

    class Meta:

        model = MedicinePrescription

        fields = [

            "id",

            # Patient
            "patient_id",
            "patient_name",

            # Doctor
            "doctor_name",

            # Medicine
            "medicine",
            "medicine_name",
            "medicine_strength",
            "medicine_strength_unit",
            "medicine_dosage_form",

            # Prescription
            "frequency",
            "duration",
            "duration_unit",
            "quantity",
            "instructions",
        ]

    # ---------------- MEDICINE NAME ----------------

    def get_medicine_name(self, obj):

        if obj.medicine:
            return obj.medicine.name

        return obj.medicine_name

class PharmacyBillItemSerializer(serializers.ModelSerializer):

    # ---------------- SERIAL NUMBER ----------------

    serial_number = serializers.SerializerMethodField()

    # ---------------- MEDICINE DETAILS ----------------

    medicine_id = serializers.IntegerField(
        source="medicine.id",
        read_only=True
    )

    medicine_name = serializers.CharField(
        source="medicine.name",
        read_only=True
    )

    # ---------------- PRESCRIPTION DETAILS ----------------

    doctor_name = serializers.CharField(
        source=(
            "prescription.consultation.appointment."
            "doctor.user_profile.name"
        ),
        read_only=True
    )

    prescription_date = serializers.SerializerMethodField()

    class Meta:

        model = PharmacyBillItem

        fields = [
            "id",

            "serial_number",

            "prescription",

            "doctor_name",
            "prescription_date",

            "medicine_id",
            "medicine_name",

            "quantity",
            "unit_price",
            "total_price",
        ]

        read_only_fields = [
            "medicine_id",
            "medicine_name",
            "quantity",
            "unit_price",
            "total_price",
        ]

    # ---------------- SERIAL NUMBER ----------------

    def get_serial_number(self, obj):

        bill_items = list(
            obj.pharmacy_bill.items.order_by("id")
        )

        return bill_items.index(obj) + 1

    # ---------------- PRESCRIPTION DATE ----------------

    def get_prescription_date(self, obj):

        return obj.prescription.consultation.consultation_date



class PharmacyBillSerializer(serializers.ModelSerializer):

    # ---------------- BILL NUMBER ----------------

    bill_number = serializers.SerializerMethodField()


    # ---------------- PATIENT DETAILS ----------------

    patient_name = serializers.CharField(
        source="patient.patient_name",
        read_only=True
    )

    patient_id = serializers.CharField(
        source="patient.patient_id",
        read_only=True
    )


    # ---------------- ISSUE DATE ----------------

    issue_date = serializers.DateTimeField(
        source="created_at",
        read_only=True
    )


    # ---------------- ITEMS ----------------

    items = PharmacyBillItemSerializer(
        many=True,
        read_only=True
    )


    class Meta:

        model = PharmacyBill

        fields = [

            "id",

            "bill_number",

            "patient",
            "patient_id",
            "patient_name",

            "subtotal",
            "gst_amount",
            "total_amount",
            "amount_paid",

            "payment_status",

            "issue_date",

            "items",
        ]

        read_only_fields = [

            "subtotal",
            "gst_amount",
            "total_amount",
            "amount_paid",
            "payment_status",
            "issue_date",
        ]


    # ---------------- BILL NUMBER ----------------

    def get_bill_number(self, obj):

        return f"PHARM-{obj.id:06d}"