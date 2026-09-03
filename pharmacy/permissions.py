from rest_framework.permissions import BasePermission


class IsPharmacist(BasePermission):

    def has_permission(self, request, view):

        # User must be logged in
        if not request.user or not request.user.is_authenticated:
            return False

        # Check user role
        try:
            return request.user.profile.role == "PHARMACIST"

        except:
            return False