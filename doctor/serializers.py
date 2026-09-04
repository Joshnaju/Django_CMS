from datetime import date

from rest_framework import serializers

from doctor.models import Consultation, LabOrder, MedicinePrescription
from receptionist.models import Patient
from django.utils import timezone
class DoctorPatientSerializer(serializers.ModelSerializer):

    age = serializers.SerializerMethodField()
    class Meta:
        model = Patient
        fields = [
            "id",
            "patient_id",
            "patient_name",
            "age",
            "gender",
            "address",
            "mobile_number",
            "email",
            "blood_group",
            "is_active",
        ]

    def get_age(self, obj):
        dob = obj.date_of_birth

        if not dob:
            return None

        today = date.today()

        age = today.year - dob.year

        if (today.month, today.day) < (dob.month, dob.day):
            age -= 1

        if age >= 1:
            return f"{age} year(s)"

        months = (today.year - dob.year) * 12 + (today.month - dob.month)

        if today.day < dob.day:
            months -= 1

        if months >= 1:
            return f"{months} month(s)"

        days = (today - dob).days

        return f"{days} day(s)"
    
class MedicinePrescriptionSerializer(serializers.ModelSerializer):

    medicine_name = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    medicine_strength = serializers.CharField(
        source="medicine.strength",
        read_only=True
    )

    medicine_strength_unit = serializers.CharField(
        source="medicine.strength_unit",
        read_only=True
    )

    medicine_dosage_form = serializers.CharField(
        source="medicine.dosage_form",
        read_only=True
    )

    class Meta:
        model = MedicinePrescription

        fields = [
            "id",
            "medicine",
            "medicine_name",
            "medicine_strength",
            "medicine_strength_unit",
            "medicine_dosage_form",
            "frequency",
            "duration",
            "duration_unit",
            "quantity",
            "instructions",
        ]

        read_only_fields = [
            "id",
            "quantity",
            "medicine_strength",
            "medicine_strength_unit",
            "medicine_dosage_form",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Medicine available in Medicine Master
        if instance.medicine:
            data["medicine_name"] = instance.medicine.name

        # Medicine not available in pharmacy
        else:
            data["medicine_name"] = instance.medicine_name

        return data

    def validate(self, attrs):

        medicine = attrs.get("medicine")
        medicine_name = attrs.get("medicine_name")

        # Neither selected nor manually entered
        if not medicine and not medicine_name:
            raise serializers.ValidationError(
                "Please select a medicine or enter a medicine name."
            )

        # If Medicine Master medicine is selected,
        # don't store a duplicate manual name.
        if medicine:
            attrs["medicine_name"] = None

        return attrs

class LabOrderSerializer(serializers.ModelSerializer):

    lab_test_name = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    class Meta:
        model = LabOrder

        fields = [
            "id",
            "lab_test",
            "lab_test_name",
            "instructions",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if instance.lab_test:
            data["lab_test_name"] = instance.lab_test.name
        else:
            data["lab_test_name"] = instance.lab_test_name

        return data

class ConsultationSerializer(serializers.ModelSerializer):

    patient_id = serializers.CharField(
        source="appointment.patient.patient_id",
        read_only=True
    )

    patient_name = serializers.CharField(
        source="appointment.patient.patient_name",
        read_only=True
    )

    patient_age = serializers.SerializerMethodField()

    patient_gender = serializers.CharField(
        source="appointment.patient.gender",
        read_only=True
    )

    patient_place = serializers.CharField(
        source="appointment.patient.address",
        read_only=True
    )

    medicine_prescriptions = MedicinePrescriptionSerializer(
        many=True,
        required=False
    )

    lab_orders = LabOrderSerializer(
        many=True,
        required=False
    )

    medical_history = serializers.SerializerMethodField()

    class Meta:
        model = Consultation

        fields = [
            "id",
            "appointment",
            "patient_id",
            "patient_name",
            "patient_age",
            "patient_gender",
            "patient_place",
            "symptoms",
            "diagnosis",
            "notes",
            "consultation_date",
            "updated_at",
            "medicine_prescriptions",
            "lab_orders",
            "medical_history",
        ]

    def get_patient_age(self, obj):

        dob = obj.appointment.patient.date_of_birth

        if not dob:
            return None

        today = timezone.localdate()

        return (
            today.year
            - dob.year
            - (
                (today.month, today.day)
                < (dob.month, dob.day)
            )
        )
    
    def get_medical_history(self, obj):

        patient = obj.appointment.patient

        previous_consultations = Consultation.objects.filter(
            appointment__patient=patient
        ).exclude(
            id=obj.id
        ).prefetch_related(
            "medicine_prescriptions",
            "medicine_prescriptions__medicine",
            "lab_orders",
            "lab_orders__lab_test",
        ).order_by(
            "-consultation_date"
        )

        return ConsultationHistorySerializer(
            previous_consultations,
            many=True
        ).data


    def create(self, validated_data):

        # -----------------------------------------
        # Get nested medicine data
        # -----------------------------------------

        medicine_data = validated_data.pop(
            "medicine_prescriptions",
            []
        )

        # -----------------------------------------
        # Get nested lab data
        # -----------------------------------------

        lab_data = validated_data.pop(
            "lab_orders",
            []
        )

        # -----------------------------------------
        # Create Consultation
        # -----------------------------------------

        consultation = Consultation.objects.create(
            **validated_data
        )

        # -----------------------------------------
        # Create Medicine Prescriptions
        # -----------------------------------------

        for medicine_data_item in medicine_data:

            medicine_obj = medicine_data_item.get("medicine")

            # -----------------------------------------
            # Available medicine
            # -----------------------------------------

            if medicine_obj:
                medicine_data_item["medicine_name"] = medicine_obj.name

            # -----------------------------------------
            # Calculate Quantity
            # -----------------------------------------

            frequency = medicine_data_item.get("frequency")
            duration = medicine_data_item.get("duration")
            duration_unit = medicine_data_item.get("duration_unit")

            quantity = None

            if frequency and duration:

                try:
                    # Example:
                    # 1-0-1 = 2 tablets per day
                    doses_per_day = sum(
                        int(value)
                        for value in frequency.split("-")
                    )

                    # Days
                    if duration_unit == "DAYS":
                        total_days = duration

                    # Weeks
                    elif duration_unit == "WEEKS":
                        total_days = duration * 7

                    # Months
                    elif duration_unit == "MONTHS":
                        total_days = duration * 30

                    else:
                        total_days = 0

                    quantity = doses_per_day * total_days

                except (ValueError, TypeError):
                    quantity = None

            # -----------------------------------------
            # Save Prescription
            # -----------------------------------------

            MedicinePrescription.objects.create(
                consultation=consultation,
                quantity=quantity,
                **medicine_data_item
            )

        # -----------------------------------------
        # Create Lab Orders
        # -----------------------------------------

        for lab_data_item in lab_data:

            lab_test_obj = lab_data_item.get("lab_test")

            # Available lab test
            if lab_test_obj:
                lab_data_item["lab_test_name"] = lab_test_obj.name

            LabOrder.objects.create(
                consultation=consultation,
                **lab_data_item
            )

        return consultation
class ConsultationHistorySerializer(serializers.ModelSerializer):
    medicine_prescriptions = MedicinePrescriptionSerializer(
        many=True,
        read_only=True
    )

    lab_orders = LabOrderSerializer(
        many=True,
        read_only=True
    )

    doctor_name = serializers.CharField(
        source="appointment.doctor.user_profile.name",
        read_only=True
    )

    department_name = serializers.CharField(
        source="appointment.doctor.department.name",
        read_only=True
    )

    appointment = serializers.IntegerField(
    source="appointment.id",
    read_only=True
    )
    class Meta:
        model = Consultation

        fields = [
            "id",
            "doctor_name",
            "department_name",
            "appointment",
            "symptoms",
            "diagnosis",
            "notes",
            "consultation_date",
            "medicine_prescriptions",
            "lab_orders",
        ]
class DoctorPatientDetailSerializer(serializers.ModelSerializer):

    age = serializers.SerializerMethodField()
    consultations = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            "id",
            "patient_id",
            "patient_name",
            "age",
            "gender",
            "address",
            "mobile_number",
            "email",
            "blood_group",
            "is_active",
            "consultations",
        ]

    def get_age(self, obj):
        dob = obj.date_of_birth

        if not dob:
            return None

        today = date.today()

        age = today.year - dob.year

        if (today.month, today.day) < (dob.month, dob.day):
            age -= 1

        if age >= 1:
            return f"{age} year(s)"

        months = (today.year - dob.year) * 12 + (today.month - dob.month)

        if today.day < dob.day:
            months -= 1

        if months >= 1:
            return f"{months} month(s)"

        days = (today - dob).days

        return f"{days} day(s)"

    def get_consultations(self, obj):
        consultations = Consultation.objects.filter(
            appointment__patient=obj
        ).select_related(
            "appointment",
            "appointment__doctor",
        ).prefetch_related(
            "medicine_prescriptions",
            "medicine_prescriptions__medicine",
            "lab_orders",
            "lab_orders__lab_test",
        ).order_by("-consultation_date")

        return ConsultationHistorySerializer(
            consultations,
            many=True,
            context=self.context
        ).data