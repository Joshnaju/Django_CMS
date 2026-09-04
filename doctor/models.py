from django.db import models

from accounts.models import UserProfile
from departments.models import Department

class Doctor(models.Model):
    user_profile = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE, related_name="doctor"
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="doctors",
    )

    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "doctor"

    def __str__(self):
        return self.user_profile.user.get_full_name()
class Consultation(models.Model):

    appointment = models.OneToOneField(
        "receptionist.Appointment",
        on_delete=models.PROTECT,
        related_name="consultation"
    )

    symptoms = models.TextField()

    diagnosis = models.TextField()

    notes = models.TextField(
        blank=True,
        null=True
    )

    consultation_date = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "consultation"

    def __str__(self):
        return (
            f"Consultation - "
            f"{self.appointment.patient.patient_id}"
        )

class MedicinePrescription(models.Model):

    consultation = models.ForeignKey(
        "doctor.Consultation",
        on_delete=models.CASCADE,
        related_name="medicine_prescriptions"
    )

    medicine = models.ForeignKey(
        "medicine_master.Medicine",
        on_delete=models.PROTECT,
        related_name="medicine_prescriptions",
        null=True,
        blank=True
    )

    medicine_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    frequency = models.CharField(
        max_length=20
    )

    duration = models.PositiveIntegerField()

    duration_unit = models.CharField(
        max_length=20,
        choices=[
            ("DAYS", "Days"),
            ("WEEKS", "Weeks"),
            ("MONTHS", "Months"),
        ]
    )

    quantity = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    instructions = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        db_table = "medicine_prescription"

    def __str__(self):
        return self.medicine.name if self.medicine else self.medicine_name
class LabOrder(models.Model):

    consultation = models.ForeignKey(
        "doctor.Consultation",
        on_delete=models.CASCADE,
        related_name="lab_orders"
    )

    lab_test = models.ForeignKey(
        "lab_master.LabTest",
        on_delete=models.PROTECT,
        related_name="lab_orders",
        null=True,      
        blank=True 
    )

    lab_test_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    instructions = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        db_table = "lab_order"

    def __str__(self):
        lab_name = (
            self.lab_test.name
            if self.lab_test
            else self.lab_test_name
        )

        return (
            f"{lab_name} - "
            f"{self.consultation.appointment.patient.patient_id}"
        )