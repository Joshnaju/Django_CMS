from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import (
    PatientViewSet,
    AppointmentViewSet,
    ConsultationBillViewSet,
    DepartmentViewSet,
    ReceptionistDoctorViewSet,
    NextAvailableSlotViewSet,
    AvailableSlotsViewSet,
    FeePreviewViewSet,
    PaidAppointmentBookingViewSet,
    ReceptionistDashboardViewSet,
)


router = DefaultRouter()

router.register(
    "patients",
    PatientViewSet,
)

router.register(
    "appointments",
    AppointmentViewSet,
)

router.register(
    "consultation-bills",
    ConsultationBillViewSet,
    basename="consultation-bills",
)

router.register(
    "departments",
    DepartmentViewSet,
    basename="receptionist-departments",
)

router.register(
    "doctors",
    ReceptionistDoctorViewSet,
    basename="receptionist-doctors",
)

router.register(
    "next-slot",
    NextAvailableSlotViewSet,
    basename="next-slot",
)

router.register(
    "available-slots",
    AvailableSlotsViewSet,
    basename="available-slots",
)

router.register(
    "fee-preview",
    FeePreviewViewSet,
    basename="fee-preview",
)

router.register(
    "paid-booking",
    PaidAppointmentBookingViewSet,
    basename="paid-booking",
)

router.register(
    "dashboard",
    ReceptionistDashboardViewSet,
    basename="receptionist-dashboard",
)


urlpatterns = [
    path("", include(router.urls)),
]