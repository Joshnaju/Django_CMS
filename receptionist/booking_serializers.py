from django.db import transaction

from rest_framework import serializers

from departments.models import Department
from doctor.models import Doctor

from .models import Patient, Appointment, ConsultationBill
from .serializers import AppointmentSerializer


# =========================================================
# DEPARTMENT SERIALIZER
# =========================================================

class DepartmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Department
        fields = [
            "id",
            "name",
        ]


# =========================================================
# DOCTOR SERIALIZER FOR RECEPTIONIST
# =========================================================

class ReceptionistDoctorSerializer(serializers.ModelSerializer):

    doctor_name = serializers.SerializerMethodField()

    department_name = serializers.CharField(
        source="department.name",
        read_only=True
    )

    class Meta:
        model = Doctor
        fields = [
            "id",
            "doctor_name",
            "department",
            "department_name",
            "consultation_fee",
        ]

    def get_doctor_name(self, obj):
        return obj.user_profile.name


# =========================================================
# PAID APPOINTMENT BOOKING SERIALIZER
# =========================================================

class PaidAppointmentBookingSerializer(serializers.Serializer):

    PAYMENT_STATUS_CHOICES = [
        ("PAID", "Paid"),
        ("UNPAID", "Unpaid"),
    ]

    patient = serializers.PrimaryKeyRelatedField(
        queryset=Patient.objects.filter(is_active=True)
    )

    doctor = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.all()
    )

    appointment_type = serializers.ChoiceField(
        choices=Appointment.APPOINTMENT_TYPE_CHOICES
    )

    appointment_date = serializers.DateField()

    appointment_time = serializers.TimeField()

    payment_status = serializers.ChoiceField(
        choices=PAYMENT_STATUS_CHOICES
    )

    def validate_payment_status(self, value):

        if value != "PAID":
            raise serializers.ValidationError(
                "Appointment cannot be booked until payment is completed."
            )

        return value

    def validate(self, attrs):

        appointment_serializer = AppointmentSerializer(
            data={
                "patient": attrs["patient"].id,
                "doctor": attrs["doctor"].id,
                "appointment_type": attrs["appointment_type"],
                "appointment_date": attrs["appointment_date"],
                "appointment_time": attrs["appointment_time"],
            }
        )

        appointment_serializer.is_valid(
            raise_exception=True
        )

        attrs["appointment_data"] = (
            appointment_serializer.validated_data
        )

        return attrs

    @transaction.atomic
    def create(self, validated_data):

        appointment_data = validated_data.pop(
            "appointment_data"
        )

        validated_data.pop(
            "payment_status"
        )

        # Appointment is created ONLY after PAID validation.
        # Appointment.save() automatically generates the token.
        appointment = Appointment.objects.create(
            **appointment_data
        )

        consultation_fee = (
            appointment.doctor.consultation_fee
        )

        previous_bill_exists = ConsultationBill.objects.filter(
            appointment__patient=appointment.patient
        ).exists()

        registration_fee = (
            0 if previous_bill_exists else 100
        )

        total_amount = (
            registration_fee + consultation_fee
        )

        # Bill is created only after the paid appointment
        # has been successfully created.
        bill = ConsultationBill.objects.create(
            appointment=appointment,
            registration_fee=registration_fee,
            consultation_fee=consultation_fee,
            total_amount=total_amount,
        )

        return {
            "appointment": appointment,
            "bill": bill,
        }

    