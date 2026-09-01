from rest_framework import serializers
from datetime import date
from .models import Patient


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


