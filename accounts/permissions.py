from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.profile.role == "ADMIN"


class IsReceptionist(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.profile.role == "RECEPTIONIST"
        )


class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.profile.role == "DOCTOR"


class IsPharmacist(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and request.user.profile.role == "PHARMACIST"
        )


class IsLabTechnician(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.profile.role == "LAB_TECHNICIAN"
        )
