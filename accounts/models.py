from django.contrib.auth.models import User
from django.db import models
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("ADMIN", "Admin"),
        ("RECEPTIONIST", "Receptionist"),
        ("DOCTOR", "Doctor"),
        ("PHARMACIST", "Pharmacist"),
        ("LAB_TECHNICIAN", "Lab Technician"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    class Meta:
        db_table = "userprofile"

    def __str__(self):
        return self.user.username
