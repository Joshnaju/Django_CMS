from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import LabTest
from .serializers import LabTestSerializer


class LabTestViewSet(viewsets.ModelViewSet):
    queryset = LabTest.objects.all()

    serializer_class = LabTestSerializer

    permission_classes = [AllowAny]
