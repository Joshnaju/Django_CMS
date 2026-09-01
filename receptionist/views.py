#from django.shortcuts import render

from rest_framework import viewsets

from .models import Patient, Appointment, ConsultationBill
from .serializers import (
    PatientSerializer,
    AppointmentSerializer,
    ConsultationBillSerializer,
)


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer

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



