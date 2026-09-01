from rest_framework import serializers

from doctor.models import Consultation, LabOrder, MedicinePrescription
from receptionist.models import Patient


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
        source="medicine.name",
        read_only=True
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

class LabOrderSerializer(serializers.ModelSerializer):

    lab_test_name = serializers.CharField(
        source="lab_test.name",
        read_only=True
    )

    class Meta:
        model = LabOrder

        fields = [
            "id",
            "lab_test",
            "lab_test_name",
            "instructions",
        ]

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

    class Meta:
        model = Consultation

        fields = [
            "id",
            "appointment",
            "patient_id",
            "patient_name",
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