from rest_framework import serializers
from datetime import date, timedelta
from .models import Patient, Appointment

class PatientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Patient
        fields = '__all__'
        read_only_fields = [
            'patient_id',
            'created_at',
            'updated_at',
        ]

    def validate_patient_name(self, value):
        name = value.strip()

        if len(name) < 3 or len(name) > 150:
            raise serializers.ValidationError(
                "Patient name must be between 3 and 150 characters."
            )

        if not all(
            char.isalpha() or char.isspace()
            for char in name
        ):
            raise serializers.ValidationError(
                "Patient name must contain only letters and spaces."
            )

        return name

    def validate_date_of_birth(self, value):
        today = date.today()

        if value > today:
            raise serializers.ValidationError(
                "Date of birth cannot be in the future."
            )

        age = (
            today.year
            - value.year
            - (
                (today.month, today.day)
                < (value.month, value.day)
            )
        )

        if age > 150:
            raise serializers.ValidationError(
                "Patient age cannot be more than 150 years."
            )

        return value

    def validate_mobile_number(self, value):
        mobile = value.strip()

        if not mobile.isdigit():
            raise serializers.ValidationError(
                "Mobile number must contain only digits."
            )

        if len(mobile) != 10:
            raise serializers.ValidationError(
                "Mobile number must contain exactly 10 digits."
            )

        if mobile[0] not in ['6', '7', '8', '9']:
            raise serializers.ValidationError(
                "Mobile number must start with 6, 7, 8, or 9."
            )

        return mobile

    def validate_email(self, value):
        if not value:
            return value

        return value.strip().lower()

    def validate_address(self, value):
        address = value.strip()

        if len(address) < 5:
            raise serializers.ValidationError(
                "Address must contain at least 5 characters."
            )

        return address


class AppointmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = [
            'token_number',
            'created_at',
            'updated_at',
        ]

    def validate(self, data):
        today = date.today()

        appointment_type = data.get('appointment_type')
        appointment_date = data.get('appointment_date')
        patient = data.get('patient')
        doctor = data.get('doctor')
        appointment_time = data.get('appointment_time')

        # Patient must be active
        if patient and not patient.is_active:
            raise serializers.ValidationError({
                "patient": "Cannot create an appointment for an inactive patient."
            })

        # Appointment cannot be in the past
        if appointment_date and appointment_date < today:
            raise serializers.ValidationError({
                "appointment_date":
                "Appointment cannot be scheduled for a past date."
            })

        # Walk-in appointments are only for today
        if appointment_type == 'WALK_IN':
            if appointment_date != today:
                raise serializers.ValidationError({
                    "appointment_date":
                    "Walk-in appointment must be for today."
                })

        # Prior booking must be at least 2 days in advance
        if appointment_type == 'PRIOR_BOOKING':
            minimum_date = today + timedelta(days=2)

            if appointment_date < minimum_date:
                raise serializers.ValidationError({
                    "appointment_date":
                    "Prior booking must be made at least 2 days in advance."
                })

        # Prevent duplicate doctor appointment slot
        if doctor and appointment_date and appointment_time:
            existing_appointment = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time
            )

            # While updating an appointment,
            # ignore the current appointment itself
            if self.instance:
                existing_appointment = existing_appointment.exclude(
                    pk=self.instance.pk
                )

            if existing_appointment.exists():
                raise serializers.ValidationError({
                    "appointment_time":
                    "This doctor already has an appointment at this date and time."
                })

        return data

    