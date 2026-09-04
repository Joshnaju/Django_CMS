from rest_framework.routers import DefaultRouter, path

from doctor.views import DoctorConsultationViewSet, DoctorDashboardView, DoctorPatientViewSet
from receptionist.views import DoctorAppointmentViewSet

router = DefaultRouter()

router.register(r"appointments",DoctorAppointmentViewSet,basename="doctor-appointments")
router.register(r"patients",DoctorPatientViewSet,basename="doctor-patients")
router.register(r"consultations",DoctorConsultationViewSet,basename="doctor-consultations")

urlpatterns=[path("dashboard/",DoctorDashboardView.as_view(), name="doctor-dashboard")]
urlpatterns = router.urls + urlpatterns