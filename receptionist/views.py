from datetime import timezone


from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Patient, Appointment, ConsultationBill
from .serializers import (
    DoctorAppointmentSerializer,
    PatientSerializer,
    AppointmentSerializer,
    ConsultationBillSerializer,
)
from .permissions import IsReceptionist


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    # permission_classes = [IsAuthenticated, IsReceptionist]
    permission_classes = []


    def get_queryset(self):
        queryset = Patient.objects.all()

        patient_id = self.request.query_params.get('patient_id')
        mobile_number = self.request.query_params.get('mobile_number')

        if patient_id:
            queryset = queryset.filter(
                patient_id__iexact=patient_id
            )

        if mobile_number:
            queryset = queryset.filter(
                mobile_number=mobile_number
            )

        return queryset.order_by('patient_id')


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    # permission_classes = [IsAuthenticated, IsReceptionist]
    permission_classes = []


    def get_queryset(self):
        queryset = Appointment.objects.all()

        appointment_date = self.request.query_params.get('date')

        if appointment_date:
            queryset = queryset.filter(
                appointment_date=appointment_date
            )

        return queryset.order_by(
            'appointment_date',
            'appointment_time',
            'token_number'
        )


class ConsultationBillViewSet(viewsets.ModelViewSet):
    queryset = ConsultationBill.objects.all()
    serializer_class = ConsultationBillSerializer
    # permission_classes = [IsAuthenticated, IsReceptionist]
    permission_classes = []


# FOR DOCTOR MODULE
class DoctorAppointmentViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = DoctorAppointmentSerializer
    permission_classes = [IsAuthenticated]
    # permission_classes = []


    def get_queryset(self):
        return Appointment.objects.filter(
            doctor__user_profile__user=self.request.user
        ).select_related(
            "patient",
            "doctor",
            "doctor__user_profile",
        ).order_by(
            "appointment_date",
            "appointment_time",
        )
    
    @action(detail=False, methods=["get"])
    def today(self, request):

        today = timezone.localdate()

        appointments = self.get_queryset().filter(
            appointment_date=today
        )

        serializer = self.get_serializer(
            appointments,
            many=True
        )

        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def upcoming(self, request):

        today = timezone.localdate()

        appointments = self.get_queryset().filter(
            appointment_date__gte=today,
            status="SCHEDULED",
        )

        serializer = self.get_serializer(
            appointments,
            many=True
        )

        return Response(serializer.data)