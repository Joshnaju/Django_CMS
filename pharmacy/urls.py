from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import (
    MedicineInventoryViewSet,
    medicine_details
)


router = DefaultRouter()

router.register(
    "medicine-inventory",
    MedicineInventoryViewSet,
    basename="medicine-inventory"
)


urlpatterns = [
    path(
        "medicine/<int:medicine_id>/",
        medicine_details,
        name="medicine-details"
    ),
]

urlpatterns += router.urls