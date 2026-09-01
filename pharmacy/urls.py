from rest_framework.routers import DefaultRouter

from .views import MedicineInventoryViewSet


router = DefaultRouter()

router.register(
    "medicine-inventory",
    MedicineInventoryViewSet,
    basename="medicine-inventory"
)

urlpatterns = router.urls