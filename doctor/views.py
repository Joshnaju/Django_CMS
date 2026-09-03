from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsDoctor
from doctor.models import Consultation
from receptionist.models import Appointment, Patient
from receptionist.serializers import PatientSerializer

from .serializers import ConsultationHistorySerializer, ConsultationSerializer, DoctorPatientDetailSerializer, DoctorPatientSerializer
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import APIView, action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
class DoctorPatientViewSet(viewsets.ReadOnlyModelViewSet):

    permission_classes = [IsAuthenticated, IsDoctor]
    serializer_class = DoctorPatientSerializer

    def get_queryset(self):

        return Patient.objects.filter(
            appointments__doctor__user_profile__user=self.request.user
        ).distinct().order_by(
            "patient_name"
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="history"
    )
    def history(self, request, pk=None):

        patient = self.get_object()

        consultations = Consultation.objects.filter(
            appointment__patient=patient,
            appointment__doctor__user_profile__user=request.user
        ).select_related(
            "appointment",
            "appointment__doctor",
            "appointment__doctor__user_profile"
        ).prefetch_related(
            "medicine_prescriptions",
            "medicine_prescriptions__medicine",
            "lab_orders",
            "lab_orders__lab_test"
        ).order_by(
            "-consultation_date"
        )

        serializer = ConsultationSerializer(
            consultations,
            many=True
        )

        return Response(serializer.data)

class DoctorConsultationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsDoctor]
    serializer_class = ConsultationSerializer

    def get_queryset(self):
        return Consultation.objects.filter(
            appointment__doctor__user_profile__user=self.request.user
        ).select_related(
            "appointment",
            "appointment__patient",
            "appointment__doctor",
        ).prefetch_related(
            "medicine_prescriptions",
            "medicine_prescriptions__medicine",
            "lab_orders",
            "lab_orders__lab_test",
        ).order_by("-consultation_date")

    @action(
        detail=False,
        methods=["get"],
        url_path="by-appointment/(?P<appointment_id>[^/.]+)"
    )
    def by_appointment(self, request, appointment_id=None):

        consultation = self.get_queryset().filter(
            appointment_id=appointment_id
        ).first()

        if not consultation:
            return Response(
                {"detail": "Consultation not found."},
                status=404
            )

        serializer = self.get_serializer(consultation)

        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path="patients"
    )
    def patients(self, request):

        consultations = self.get_queryset()

        patients = Patient.objects.filter(
            appointments__consultation__in=consultations
        ).distinct().order_by("patient_id")

        serializer = DoctorPatientSerializer(
            patients,
            many=True
        )

        return Response(serializer.data)

    @action(
    detail=False,
    methods=["get"],
    url_path=r"patients/(?P<patient_id>[^/.]+)/consultation/(?P<appointment_id>[^/.]+)"
    )
    def patient_consultation(
        self,
        request,
        patient_id=None,
        appointment_id=None
    ):
        consultation = Consultation.objects.filter(
            appointment_id=appointment_id,
            appointment__patient_id=patient_id
        ).select_related(
            "appointment",
            "appointment__patient",
            "appointment__doctor",
        ).prefetch_related(
            "medicine_prescriptions",
            "medicine_prescriptions__medicine",
            "lab_orders",
            "lab_orders__lab_test",
        ).first()

        if not consultation:
            return Response(
                {"detail": "Consultation not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ConsultationHistorySerializer(
            consultation,
            context={"request": request}
        )

        return Response(serializer.data)
    @action(
        detail=False,
        methods=["get"],
        url_path="history-by-appointment/(?P<appointment_id>[^/.]+)"
    )
    def history_by_appointment(self, request, appointment_id=None):
        appointment = get_object_or_404(
            Appointment,
            id=appointment_id,
            doctor__user_profile__user=request.user
        )

        previous_consultations = Consultation.objects.filter(
            appointment__patient=appointment.patient
        ).prefetch_related(
            "medicine_prescriptions",
            "medicine_prescriptions__medicine",
            "lab_orders",
            "lab_orders__lab_test",
        ).order_by("-consultation_date")

        serializer = ConsultationHistorySerializer(
            previous_consultations,
            many=True
        )

        return Response(serializer.data)


    @action(
        detail=False,
        methods=["get"],
        url_path=r"patients/(?P<patient_id>[^/.]+)"
    )
    def patient_detail(self, request, patient_id=None):

        consultations = self.get_queryset()

        patient = get_object_or_404(
            Patient,
            id=patient_id
        )

        # Make sure this doctor has consulted this patient
        has_consultation = consultations.filter(
            appointment__patient=patient
        ).exists()

        if not has_consultation:
            return Response(
                {"detail": "Patient not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = DoctorPatientDetailSerializer(
            patient,
            context={"request": request}
        )

        return Response(serializer.data)

    def perform_create(self, serializer):
        appointment = serializer.validated_data["appointment"]

        if appointment.doctor.user_profile.user != self.request.user:
            raise PermissionDenied(
                "You can only create a consultation for your own appointment."
            )

        consultation = serializer.save()

        appointment.status = "COMPLETED"
        appointment.save(update_fields=["status"])

class DoctorDashboardView(APIView):

    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request):

        # Logged-in doctor's appointments
        appointments = Appointment.objects.filter(
            doctor__user_profile__user=request.user
        )

        # Today's date
        today = timezone.localdate()

        # Total unique patients consulted by this doctor
        total_patients = appointments.filter(
            consultation__isnull=False
        ).values(
            "patient_id"
        ).distinct().count()

        # Today's appointments
        today_appointments = appointments.filter(
            appointment_date=today
        )

        # Completed appointments today
        completed_today = today_appointments.filter(
            status="COMPLETED"
        ).count()

        # Scheduled appointments today
        scheduled_today = today_appointments.filter(
            status="SCHEDULED"
        ).count()

        return Response({
            "total_patients": total_patients,
            "today_appointments": today_appointments.count(),
            "completed_today": completed_today,
            "scheduled_today": scheduled_today,
        })

