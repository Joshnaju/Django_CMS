from datetime import date

from django.db.models import Q
from rest_framework import status, viewsets
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
from .scheduling import (
    get_india_now,
    get_next_available_slot,
    get_available_slots,
    WORK_END,
)


# =========================================================
# PATIENT MANAGEMENT
# =========================================================

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

        patient_name = self.request.query_params.get(
            "patient_name"
        )

        mobile_number = self.request.query_params.get(
            "mobile_number"
        )

        # Search by unique Patient ID
        if patient_id:
            queryset = queryset.filter(
                patient_id__iexact=patient_id.strip()
            )

        # Search by Patient Name
        if patient_name:
            queryset = queryset.filter(
                patient_name__icontains=patient_name.strip()
            )

        # Search by Mobile Number
        if mobile_number:
            queryset = queryset.filter(
                mobile_number=mobile_number.strip()
            )

        return queryset.order_by("patient_id")


# =========================================================
# APPOINTMENT MANAGEMENT
# =========================================================

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [
        IsAuthenticated,
        IsReceptionist,
    ]

    def get_queryset(self):
        queryset = Appointment.objects.select_related(
            "patient",
            "doctor",
            "doctor__user_profile",
            "doctor__department",
        )

        india_now = get_india_now()

        today = india_now.date()

        current_time = india_now.time()

        # -------------------------------------------------
        # DATE FILTER
        # -------------------------------------------------

        appointment_date = self.request.query_params.get(
            "date"
        )

        if appointment_date:
            queryset = queryset.filter(
                appointment_date=appointment_date
            )

        # -------------------------------------------------
        # APPOINTMENT TYPE FILTER
        # -------------------------------------------------

        appointment_type = self.request.query_params.get(
            "appointment_type"
        )

        if appointment_type:
            queryset = queryset.filter(
                appointment_type=appointment_type
            )

        # -------------------------------------------------
        # STATUS FILTER
        # -------------------------------------------------

        status_value = self.request.query_params.get(
            "status"
        )

        if status_value:
            queryset = queryset.filter(
                status=status_value
            )

        # -------------------------------------------------
        # VIEW FILTER
        # -------------------------------------------------

        view_type = self.request.query_params.get(
            "view"
        )

        # =================================================
        # VIEW AND EDIT APPOINTMENTS
        # =================================================
        #
        # Only:
        # - active patients
        # - upcoming appointments
        #
        # Inactive patients are NOT displayed here.
        #
        # Their appointment records are NOT deleted.
        # They can still remain in Appointment Log.
        # =================================================

        if view_type == "upcoming":
            queryset = queryset.filter(
                patient__is_active=True
            ).filter(
                Q(
                    appointment_date__gt=today
                )
                |
                Q(
                    appointment_date=today,
                    appointment_time__gt=current_time,
                )
            )

        # =================================================
        # APPOINTMENT LOG
        # =================================================

        elif view_type == "log":
            queryset = queryset.filter(
                Q(
                    appointment_date__lt=today
                )
                |
                Q(
                    appointment_date=today,
                    appointment_time__lte=current_time,
                )
            )

        return queryset.order_by(
            "appointment_date",
            "appointment_time",
            "token_number",
        )


# =========================================================
# CONSULTATION BILL MANAGEMENT
# =========================================================

class ConsultationBillViewSet(
    viewsets.ReadOnlyModelViewSet
):
    queryset = ConsultationBill.objects.all()
    serializer_class = ConsultationBillSerializer
    permission_classes = [
        IsAuthenticated,
        IsReceptionist,
    ]

    def get_queryset(self):
        queryset = ConsultationBill.objects.select_related(
            "appointment",
            "appointment__patient",
            "appointment__doctor",
            "appointment__doctor__user_profile",
            "appointment__doctor__department",
        )

        # -------------------------------------------------
        # BILL ID
        # Example: CB0001
        # -------------------------------------------------

        bill_id = self.request.query_params.get(
            "bill_id"
        )

        if bill_id:
            bill_id = bill_id.strip().upper()

            if bill_id.startswith("CB"):
                bill_id = bill_id[2:]

            if bill_id.isdigit():
                queryset = queryset.filter(
                    id=int(bill_id)
                )
            else:
                return queryset.none()

        # -------------------------------------------------
        # APPOINTMENT ID
        # Example: APT0001
        # -------------------------------------------------

        appointment_id = self.request.query_params.get(
            "appointment_id"
        )

        if appointment_id:
            appointment_id = appointment_id.strip().upper()

            if appointment_id.startswith("APT"):
                appointment_id = appointment_id[3:]

            if appointment_id.isdigit():
                queryset = queryset.filter(
                    appointment_id=int(appointment_id)
                )
            else:
                return queryset.none()

        # -------------------------------------------------
        # PATIENT ID
        # -------------------------------------------------

        patient_id = self.request.query_params.get(
            "patient_id"
        )

        if patient_id:
            queryset = queryset.filter(
                appointment__patient__patient_id__iexact=(
                    patient_id.strip()
                )
            )

        # -------------------------------------------------
        # PATIENT NAME
        # -------------------------------------------------

        patient_name = self.request.query_params.get(
            "patient_name"
        )

        if patient_name:
            queryset = queryset.filter(
                appointment__patient__patient_name__icontains=(
                    patient_name.strip()
                )
            )

        # -------------------------------------------------
        # DOCTOR NAME
        # -------------------------------------------------

        doctor_name = self.request.query_params.get(
            "doctor_name"
        )

        if doctor_name:
            queryset = queryset.filter(
                appointment__doctor__user_profile__name__icontains=(
                    doctor_name.strip()
                )
            )

        # -------------------------------------------------
        # BILL DATE
        # -------------------------------------------------

        bill_date = self.request.query_params.get(
            "date"
        )

        if bill_date:
            queryset = queryset.filter(
                created_at__date=bill_date
            )

        return queryset.order_by(
            "-created_at"
        )


# =========================================================
# RECEPTIONIST DASHBOARD
# =========================================================

class ReceptionistDashboardViewSet(
    viewsets.ViewSet
):
    permission_classes = [
        IsAuthenticated,
        IsReceptionist,
    ]

    def list(self, request):
        india_now = get_india_now()

        today = india_now.date()

        # Total patients registered till date
        total_patients = Patient.objects.count()

        # Today's appointments excluding cancelled ones
        today_appointments = Appointment.objects.filter(
            appointment_date=today
        ).exclude(
            status="CANCELLED"
        ).count()

        return Response(
            {
                "total_patients": total_patients,
                "today_appointments": today_appointments,
                "date": today.isoformat(),
            }
        )


# =========================================================
# DEPARTMENT LIST
# =========================================================

class DepartmentViewSet(
    viewsets.ReadOnlyModelViewSet
):
    queryset = Department.objects.all().order_by(
        "name"
    )

    serializer_class = DepartmentSerializer

    permission_classes = [
        IsAuthenticated,
        IsReceptionist,
    ]


# =========================================================
# DOCTOR LIST FOR RECEPTIONIST
# =========================================================

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
            "user_profile__name"
        )


# =========================================================
# NEXT AVAILABLE SLOT
# WALK-IN APPOINTMENTS
# =========================================================

class NextAvailableSlotViewSet(
    viewsets.ViewSet
):
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
            india_now = get_india_now()

            if (
                selected_date == india_now.date()
                and india_now.time() >= WORK_END
            ):
                message = (
                    "Today's consultation hours are over."
                )
            else:
                message = (
                    "All appointment slots are filled."
                )

            return Response(
                {
                    "message": message,
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


# =========================================================
# AVAILABLE SLOT LIST
# PRIOR BOOKING + APPOINTMENT EDIT
# =========================================================

class AvailableSlotsViewSet(
    viewsets.ViewSet
):
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

        appointment_id = request.query_params.get(
            "appointment"
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

        exclude_appointment = None

        if appointment_id:
            try:
                exclude_appointment = Appointment.objects.get(
                    id=appointment_id
                )

            except Appointment.DoesNotExist:
                return Response(
                    {
                        "message": (
                            "Appointment not found."
                        )
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

        slots = get_available_slots(
            doctor,
            selected_date,
            exclude_appointment=exclude_appointment,
        )

        return Response(
            {
                "available_slots": [
                    slot.strftime("%H:%M")
                    for slot in slots
                ],
                "message": (
                    "All appointment slots are filled."
                    if not slots
                    else ""
                ),
            }
        )


# =========================================================
# FEE PREVIEW
# =========================================================

class FeePreviewViewSet(
    viewsets.ViewSet
):
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
                    "message": (
                        "Active patient not found."
                    )
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
            0
            if previous_bill_exists
            else 100
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


# =========================================================
# PAID APPOINTMENT BOOKING
# =========================================================

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

        appointment = result[
            "appointment"
        ]

        bill = result[
            "bill"
        ]

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