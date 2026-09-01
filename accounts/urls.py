from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import UserProfileViewSet, LoginView

router = DefaultRouter()

router.register("profiles", UserProfileViewSet, basename="profiles")

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
]

urlpatterns += router.urls
