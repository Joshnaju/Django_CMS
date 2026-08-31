from django.contrib.auth import authenticate
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from doctor.models import Doctor

from .models import UserProfile
from .serializers import UserProfileSerializer, LoginSerializer
from rest_framework.permissions import AllowAny


class UserProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):

        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            username = serializer.validated_data["username"]
            password = serializer.validated_data["password"]

            # Authenticate user
            user = authenticate(username=username, password=password)

            # Invalid credentials
            if user is None:
                return Response(
                    {"message": "Invalid username or password"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # Get UserProfile
            try:
                profile = UserProfile.objects.get(user=user)

            except UserProfile.DoesNotExist:
                return Response(
                    {"message": "User profile not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            # Basic response
            response_data = {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "username": user.username,
                "name": profile.name,
                "role": profile.role,
            }

            # Doctor-specific details
            if profile.role == "DOCTOR":
                try:
                    doctor = Doctor.objects.get(user_profile=profile)

                    response_data["department"] = doctor.department_id

                    response_data["consultation_fee"] = str(doctor.consultation_fee)

                except Doctor.DoesNotExist:
                    response_data["department"] = None

                    response_data["consultation_fee"] = None

            else:
                response_data["department"] = None

                response_data["consultation_fee"] = None

            return Response(response_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
