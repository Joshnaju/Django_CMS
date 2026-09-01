from rest_framework.permissions import BasePermission


class IsReceptionist(BasePermission):
    message = "Only receptionists are allowed to access this resource."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if not hasattr(user, 'profile'):
            return False

        return user.profile.role == 'RECEPTIONIST'






