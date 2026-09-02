from datetime import date, timezone

from rest_framework.decorators import action
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsDoctor
from departments.models import Department
from doctor.models import Doctor

from .models import Patient, Appointment, ConsultationBill
from .serializers import (
    DoctorAppointmentSerializer,
    PatientSerializer,
    AppointmentSerializer,
    ConsultationBillSerializer,
)
from .booking_serializers import (
    DepartmentSerializer,
    ReceptionistDoctorSerializer,
    PaidAppointmentBookingSerializer,
)
from .permissions import IsReceptionist
from .scheduling import get_next_available_slot


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [
        IsAuthenticated,
        IsReceptionist,
    ]

    def get_queryset(self):
        queryset = Patient.objects.all()

        patient_id = self.request.query_params.get(
            "patient_id"
        )

        mobile_number = self.request.query_params.get(
            "mobile_number"
        )

        if patient_id:
            queryset = queryset.filter(
                patient_id__iexact=patient_id
            )

        if mobile_number:
            queryset = queryset.filter(
                mobile_number=mobile_number
            )

        return queryset.order_by("patient_id")


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [
        IsAuthenticated,
        IsReceptionist,
    ]

    def get_queryset(self):
        queryset = Appointment.objects.all()

        appointment_date = self.request.query_params.get(
            "date"
        )

        if appointment_date:
            queryset = queryset.filter(
                appointment_date=appointment_date
            )

        return queryset.order_by(
            "appointment_date",
            "appointment_time",
            "token_number",
        )


class ConsultationBillViewSet(viewsets.ModelViewSet):
    queryset = ConsultationBill.objects.all()
    serializer_class = ConsultationBillSerializer
    permission_classes = [
        IsAuthenticated,
        IsReceptionist,
    ]


# =========================================================
# RECEPTIONIST BOOKING SUPPORT
# =========================================================

class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all().order_by("name")
    serializer_class = DepartmentSerializer
    permission_classes = [
        IsAuthenticated,
        IsReceptionist,
    ]


class ReceptionistDoctorViewSet(
    viewsets.ReadOnlyModelViewSet
):
    serializer_class = ReceptionistDoctorSerializer
    permission_classes = [
        IsAuthenticated,
        IsReceptionist,
    ]

    def get_queryset(self):
        queryset = Doctor.objects.select_related(
            "user_profile",
            "user_profile__user",
            "department",
        )

        department_id = self.request.query_params.get(
            "department"
        )

        if department_id:
            queryset = queryset.filter(
                department_id=department_id
            )

        return queryset.order_by(
            "user_profile__user__first_name"
        )


class NextAvailableSlotViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
        IsReceptionist,
    ]

    def list(self, request):
        doctor_id = request.query_params.get(
            "doctor"
        )

        appointment_date = request.query_params.get(
            "date"
        )

        if not doctor_id or not appointment_date:
            return Response(
                {
                    "message": (
                        "Doctor and date are required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            doctor = Doctor.objects.get(
                id=doctor_id
            )
        except Doctor.DoesNotExist:
            return Response(
                {
                    "message": "Doctor not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            selected_date = date.fromisoformat(
                appointment_date
            )
        except ValueError:
            return Response(
                {
                    "message": "Invalid date."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        next_slot = get_next_available_slot(
            doctor,
            selected_date,
        )

        if next_slot is None:
            return Response(
                {
                    "message": (
                        "All appointment slots are filled."
                    ),
                    "next_slot": None,
                }
            )

        return Response(
            {
                "next_slot": next_slot.strftime(
                    "%H:%M"
                )
            }
        )

class FeePreviewViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
        IsReceptionist,
    ]

    def list(self, request):
        patient_id = request.query_params.get(
            "patient"
        )

        doctor_id = request.query_params.get(
            "doctor"
        )

        if not patient_id or not doctor_id:
            return Response(
                {
                    "message": (
                        "Patient and doctor are required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            patient = Patient.objects.get(
                id=patient_id,
                is_active=True,
            )
        except Patient.DoesNotExist:
            return Response(
                {
                    "message": "Patient not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            doctor = Doctor.objects.get(
                id=doctor_id
            )
        except Doctor.DoesNotExist:
            return Response(
                {
                    "message": "Doctor not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        previous_bill_exists = (
            ConsultationBill.objects.filter(
                appointment__patient=patient
            ).exists()
        )

        registration_fee = (
            0 if previous_bill_exists else 100
        )

        consultation_fee = (
            doctor.consultation_fee
        )

        total_amount = (
            registration_fee
            + consultation_fee
        )

        return Response(
            {
                "registration_fee": (
                    f"{registration_fee:.2f}"
                ),
                "consultation_fee": (
                    f"{consultation_fee:.2f}"
                ),
                "total_amount": (
                    f"{total_amount:.2f}"
                ),
            }
        )

class PaidAppointmentBookingViewSet(
    viewsets.ViewSet
):
    permission_classes = [
        IsAuthenticated,
        IsReceptionist,
    ]

    def create(self, request):
        serializer = PaidAppointmentBookingSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        result = serializer.save()

        appointment = result["appointment"]
        bill = result["bill"]

        return Response(
            {
                "message": (
                    "Payment confirmed and appointment "
                    "booked successfully."
                ),
                "appointment": AppointmentSerializer(
                    appointment
                ).data,
                "bill": ConsultationBillSerializer(
                    bill
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


# =========================================================
# FOR DOCTOR MODULE
# =========================================================

class DoctorAppointmentViewSet(
    viewsets.ReadOnlyModelViewSet
):
    serializer_class = DoctorAppointmentSerializer
    permission_classes = [
        IsAuthenticated,
        IsDoctor,
    ]

    def get_queryset(self):
        queryset = Appointment.objects.filter(
            doctor__user_profile__user=self.request.user
        ).select_related(
            "patient",
            "doctor",
            "doctor__user_profile",
        ).order_by(
            "appointment_date",
            "appointment_time",
        )

        # Date filter
        selected_date = self.request.query_params.get(
            "date"
        )

        if selected_date:
            queryset = queryset.filter(
                appointment_date=selected_date
            )

        # Status filter
        status_value = self.request.query_params.get(
            "status"
        )

        if status_value:
            queryset = queryset.filter(
                status=status_value
            )

        return queryset


