from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import (
    MedicineInventoryViewSet,
    medicine_details,
    prescription_search,
    create_pharmacy_bill,
    pay_pharmacy_bill
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

    path(
        "prescriptions/",
        prescription_search,
        name="prescription-search"
    ),

    path(
        "bills/",
        create_pharmacy_bill,
        name="create-pharmacy-bill"
    ),

    path(
        "bills/<int:bill_id>/pay/",
        pay_pharmacy_bill,
        name="pay-pharmacy-bill"
    ),
]

urlpatterns += router.urls