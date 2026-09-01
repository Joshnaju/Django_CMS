from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import MedicineInventory
from .serializers import MedicineInventorySerializer


class MedicineInventoryViewSet(viewsets.ModelViewSet):

    queryset = MedicineInventory.objects.all()

    serializer_class = MedicineInventorySerializer

    permission_classes = [AllowAny]