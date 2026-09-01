from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PatientViewSet, AppointmentViewSet


router = DefaultRouter()
router.register('patients', PatientViewSet)
router.register('appointments', AppointmentViewSet)


urlpatterns = [
    path('', include(router.urls)),
]





