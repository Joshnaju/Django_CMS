from django.db import models
from doctor.models import Doctor


class Patient(models.Model):

    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
    ]

    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]

    patient_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False
    )

    patient_name = models.CharField(
        max_length=150
    )

    date_of_birth = models.DateField()

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES
    )

    address = models.TextField()

    mobile_number = models.CharField(
        max_length=10
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    blood_group = models.CharField(
        max_length=3,
        choices=BLOOD_GROUP_CHOICES,
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = 'patient'

    def save(self, *args, **kwargs):
        if not self.patient_id:
            last_patient = Patient.objects.order_by('-id').first()

            if last_patient:
                next_number = last_patient.id + 1
            else:
                next_number = 1

            self.patient_id = f"PAT{next_number:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient_id} - {self.patient_name}"

    
class Appointment(models.Model):

    APPOINTMENT_TYPE_CHOICES = [
        ('WALK_IN', 'Walk-in'),
        ('PRIOR_BOOKING', 'Prior Booking'),
    ]

    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name='appointments'
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.PROTECT,
        related_name='appointments'
    )

    appointment_type = models.CharField(
        max_length=20,
        choices=APPOINTMENT_TYPE_CHOICES
    )

    appointment_date = models.DateField()

    appointment_time = models.TimeField()

    token_number = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='SCHEDULED'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = 'appointment'

    def save(self, *args, **kwargs):
        if not self.token_number:
            last_appointment = Appointment.objects.filter(
                doctor=self.doctor,
                appointment_date=self.appointment_date
            ).order_by('-token_number').first()

            if last_appointment and last_appointment.token_number:
                self.token_number = last_appointment.token_number + 1
            else:
                self.token_number = 1

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.patient.patient_id} - "
            f"{self.doctor} - "
            f"{self.appointment_date}"
        )



