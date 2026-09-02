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

    medicine_prescriptions = MedicinePrescriptionSerializer(
        many=True,
        required=False
    )

    lab_orders = LabOrderSerializer(
        many=True,
        required=False
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
        ]

    def create(self, validated_data):

        medicine_data = validated_data.pop(
            "medicine_prescriptions",
            []
        )

        lab_data = validated_data.pop(
            "lab_orders",
            []
        )

        consultation = Consultation.objects.create(
            **validated_data
        )

        for medicine in medicine_data:

            MedicinePrescription.objects.create(
                consultation=consultation,
                **medicine
            )

        for lab in lab_data:

            LabOrder.objects.create(
                consultation=consultation,
                **lab
            )

        return consultation

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