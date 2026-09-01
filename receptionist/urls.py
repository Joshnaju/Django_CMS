from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PatientViewSet,
    AppointmentViewSet,
    ConsultationBillViewSet,
)


router = DefaultRouter()
router.register('patients', PatientViewSet)
router.register('appointments', AppointmentViewSet)
router.register('consultation-bills', ConsultationBillViewSet)


urlpatterns = [
    path('', include(router.urls)),
]





