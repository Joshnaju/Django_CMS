from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Medicine
from .serializers import MedicineSerializer


class MedicineViewSet(viewsets.ModelViewSet):
    queryset = Medicine.objects.all()

    serializer_class = MedicineSerializer

    permission_classes = [AllowAny]
