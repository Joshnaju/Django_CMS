from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('departments.urls')),
    path('api/accounts/', include('accounts.urls')),
    path("api/token/refresh/",TokenRefreshView.as_view(),name="token_refresh"),
]
