from rest_framework.routers import DefaultRouter

from doctor.views import DoctorConsultationViewSet, DoctorPatientViewSet
from receptionist.views import DoctorAppointmentViewSet

router = DefaultRouter()

router.register(r"appointments",DoctorAppointmentViewSet,basename="doctor-appointments")
router.register(r"patients",DoctorPatientViewSet,basename="doctor-patients")
router.register(r"consultations",DoctorConsultationViewSet,basename="doctor-consultations")

urlpatterns = router.urls