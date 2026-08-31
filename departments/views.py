from rest_framework import viewsets
from .models import Department
from .serializers import DepartmentSerializer

class DepartmentViewSet(viewsets.ModelViewSet):
    permission_classes = []
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer