from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import (
    MedicineInventoryViewSet,
    medicine_details,
    prescription_search,
    create_pharmacy_bill,
    pay_pharmacy_bill,
    pharmacy_sales_report,
    low_stock_alert,
    search_medicine
)


router = DefaultRouter()

router.register(
    "medicine-inventory",
    MedicineInventoryViewSet,
    basename="medicine-inventory"
)


urlpatterns = [
    path(
        "medicine/search/",
        search_medicine,
        name="search-medicine"
    ),

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

    path(
        "reports/sales/",
        pharmacy_sales_report,
        name="pharmacy-sales-report"
    ),

    path(
        "alerts/low-stock/",
        low_stock_alert,
        name="low-stock-alert"
    ),
]

urlpatterns += router.urls