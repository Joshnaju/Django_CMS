from datetime import date, timedelta

from rest_framework import serializers

from .models import Patient, Appointment, ConsultationBill
from .scheduling import get_india_now, is_valid_appointment_slot
from datetime import date
from rest_framework import serializers
# =========================================================
# PATIENT SERIALIZER
# =========================================================

class PatientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Patient
        fields = "__all__"
        read_only_fields = [
            "patient_id",
            "created_at",
            "updated_at",
        ]

    def validate_patient_name(self, value):
        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "Patient name must contain at least 3 characters."
            )

        if not all(
            char.isalpha() or char.isspace()
            for char in value
        ):
            raise serializers.ValidationError(
                "Patient name must contain only letters and spaces."
            )

        return value

    def validate_date_of_birth(self, value):
        if value > date.today():
            raise serializers.ValidationError(
                "Date of birth cannot be in the future."
            )

        try:
            oldest_allowed_date = date(
                date.today().year - 150,
                date.today().month,
                date.today().day,
            )
        except ValueError:
            oldest_allowed_date = date(
                date.today().year - 150,
                date.today().month,
                28,
            )

        if value < oldest_allowed_date:
            raise serializers.ValidationError(
                "Patient age cannot be more than 150 years."
            )

        return value

    def validate_mobile_number(self, value):
        value = value.strip()

        if not value.isdigit():
            raise serializers.ValidationError(
                "Mobile number must contain only digits."
            )

        if len(value) != 10:
            raise serializers.ValidationError(
                "Mobile number must contain exactly 10 digits."
            )

        if value[0] not in ["6", "7", "8", "9"]:
            raise serializers.ValidationError(
                "Mobile number must start with 6, 7, 8, or 9."
            )

        return value

    def validate_address(self, value):
        value = value.strip()

        if len(value) < 5:
            raise serializers.ValidationError(
                "Address must contain at least 5 characters."
            )

        return value

    def validate_email(self, value):
        if value:
            return value.strip().lower()

        return value

    def validate(self, attrs):
        if self.instance is None:
            patient_name = attrs.get("patient_name")
            date_of_birth = attrs.get("date_of_birth")
            mobile_number = attrs.get("mobile_number")

            if (
                patient_name
                and date_of_birth
                and mobile_number
                and Patient.objects.filter(
                    patient_name__iexact=patient_name.strip(),
                    date_of_birth=date_of_birth,
                    mobile_number=mobile_number,
                ).exists()
            ):
                raise serializers.ValidationError(
                    "Patient already exists."
                )

        return attrs


# =========================================================
# APPOINTMENT SERIALIZER
# =========================================================

class AppointmentSerializer(serializers.ModelSerializer):

    patient_name = serializers.CharField(
        source="patient.patient_name",
        read_only=True,
    )

    doctor_name = serializers.CharField(
        source="doctor.user_profile.name",
        read_only=True,
    )

    class Meta:
        model = Appointment
        fields = "__all__"
        read_only_fields = [
            "token_number",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        today = get_india_now().date()

        patient = attrs.get(
            "patient",
            getattr(self.instance, "patient", None),
        )

        doctor = attrs.get(
            "doctor",
            getattr(self.instance, "doctor", None),
        )

        appointment_type = attrs.get(
            "appointment_type",
            getattr(self.instance, "appointment_type", None),
        )

        appointment_date = attrs.get(
            "appointment_date",
            getattr(self.instance, "appointment_date", None),
        )

        appointment_time = attrs.get(
            "appointment_time",
            getattr(self.instance, "appointment_time", None),
        )

        if patient and not patient.is_active:
            raise serializers.ValidationError(
                "Cannot create an appointment for an inactive patient."
            )

        if appointment_date and appointment_date < today:
            raise serializers.ValidationError(
                "Appointment date cannot be in the past."
            )

        if (
            appointment_type == "WALK_IN"
            and appointment_date
            and appointment_date != today
        ):
            raise serializers.ValidationError(
                "Walk-in appointments must be booked for today."
            )

        if (
            appointment_type == "PRIOR_BOOKING"
            and appointment_date
        ):
            tomorrow = today + timedelta(days=1)
            day_after_tomorrow = today + timedelta(days=2)

            if appointment_date not in [
                tomorrow,
                day_after_tomorrow,
            ]:
                raise serializers.ValidationError(
                    "Prior booking can only be made for the next 2 days."
                )

        if doctor and appointment_date and appointment_time:
            duplicate_slot = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
            )

            if self.instance:
                duplicate_slot = duplicate_slot.exclude(
                    pk=self.instance.pk
                )

            if duplicate_slot.exists():
                raise serializers.ValidationError(
                    "This doctor already has an appointment at this date and time."
                )

        if (
            self.instance is None
            and doctor
            and appointment_date
            and appointment_time
        ):
            if not is_valid_appointment_slot(
                doctor,
                appointment_date,
                appointment_time,
            ):
                raise serializers.ValidationError(
                    "Please select the next available appointment time slot."
                )

        return attrs


# =========================================================
# CONSULTATION BILL SERIALIZER
# =========================================================

class ConsultationBillSerializer(serializers.ModelSerializer):

    class Meta:
        model = ConsultationBill
        fields = "__all__"
        read_only_fields = [
            "registration_fee",
            "consultation_fee",
            "total_amount",
            "created_at",
        ]

    def validate_appointment(self, appointment):
        if ConsultationBill.objects.filter(
            appointment=appointment
        ).exists():
            raise serializers.ValidationError(
                "A consultation bill already exists for this appointment."
            )

        return appointment

    def create(self, validated_data):
        appointment = validated_data["appointment"]

        consultation_fee = appointment.doctor.consultation_fee

        previous_bill_exists = ConsultationBill.objects.filter(
            appointment__patient=appointment.patient
        ).exists()

        registration_fee = (
            0 if previous_bill_exists else 100
        )

        total_amount = (
            registration_fee + consultation_fee
        )

        return ConsultationBill.objects.create(
            appointment=appointment,
            registration_fee=registration_fee,
            consultation_fee=consultation_fee,
            total_amount=total_amount,
        )


# =========================================================
# FOR DOCTOR MODULE
# =========================================================

class DoctorAppointmentSerializer(serializers.ModelSerializer):

    patient_id = serializers.CharField(
        source="patient.patient_id",
        read_only=True
    )

    patient_name = serializers.CharField(
        source="patient.patient_name",
        read_only=True
    )

    patient_age = serializers.SerializerMethodField()

    patient_gender = serializers.CharField(
        source="patient.gender",
        read_only=True
    )

    patient_place = serializers.CharField(
        source="patient.address",
        read_only=True
    )

    patient_mobile = serializers.CharField(
        source="patient.mobile_number",
        read_only=True
    )

    patient_email = serializers.CharField(
        source="patient.email",
        read_only=True
    )

    patient_blood_group = serializers.CharField(
        source="patient.blood_group",
        read_only=True
    )

    doctor_name = serializers.CharField(
        source="doctor.user_profile.name",
         read_only=True
    )
    
    def get_patient_age(self, obj):
        dob = obj.patient.date_of_birth

        if not dob:
            return None

        today = date.today()

        age = today.year - dob.year

        if (today.month, today.day) < (dob.month, dob.day):
            age -= 1

        if age >= 1:
            return f"{age} year(s)"

        months = (today.year - dob.year) * 12 + (today.month - dob.month)

        if today.day < dob.day:
            months -= 1

        if months >= 1:
            return f"{months} month(s)"

        days = (today - dob).days

        return f"{days} day(s)"

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient_id",
            "patient_name",
            "patient_age",
            "patient_gender",
            "patient_place",
            "patient_mobile",
            "patient_email",
            "patient_blood_group",
            "doctor_name",
            "appointment_type",
            "appointment_date",
            "appointment_time",
            "token_number",
            "status",
            "created_at",
            "updated_at",
        ]