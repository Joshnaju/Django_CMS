from rest_framework import serializers
from .models import LabTest


class LabTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabTest

        fields = [
            "id",
            "name",
            "description",
            "normal_range",
            "unit",
            "price",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]
