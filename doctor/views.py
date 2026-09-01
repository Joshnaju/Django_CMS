from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsDoctor
from doctor.models import Consultation
from receptionist.models import Patient

from .serializers import ConsultationSerializer, DoctorPatientSerializer
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response
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

class DoctorConsultationViewSet(
    viewsets.ModelViewSet
):

    permission_classes = [IsAuthenticated,IsDoctor]

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
        ).order_by(
            "-consultation_date"
        )

    def perform_create(self, serializer):

        appointment = serializer.validated_data["appointment"]

        if appointment.doctor.user_profile.user != self.request.user:

            raise PermissionDenied(
                "You can only create a consultation for your own appointment."
            )

        serializer.save()