from rest_framework import serializers

from doctor.models import Consultation, LabOrder, MedicinePrescription
from receptionist.models import Patient
from django.utils import timezone


class DoctorPatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            "id",
            "patient_id",
            "patient_name",
            "date_of_birth",
            "gender",
            "address",
            "mobile_number",
            "email",
            "blood_group",
            "is_active",
        ]

    
class MedicinePrescriptionSerializer(serializers.ModelSerializer):

    medicine_name = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    class Meta:
        model = MedicinePrescription
        fields = [
            "id",
            "medicine",
            "medicine_name",
            "dosage",
            "frequency",
            "duration",
            "instructions",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Available medicine → get name from Medicine table
        if instance.medicine:
            data["medicine_name"] = instance.medicine.name

        # Not available → use database medicine_name
        else:
            data["medicine_name"] = instance.medicine_name

        return data

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

            # Available medicine
            if medicine_obj:
                medicine_data_item["medicine_name"] = medicine_obj.name

            MedicinePrescription.objects.create(
                consultation=consultation,
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
    class Meta:
        model = Consultation

        fields = [
            "id",
            "doctor_name",
            "department_name",
            "symptoms",
            "diagnosis",
            "notes",
            "consultation_date",
            "medicine_prescriptions",
            "lab_orders",
        ]
