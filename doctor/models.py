from django.db import models
from accounts.models import UserProfile
from departments.models import Department


class Doctor(models.Model):
    user_profile = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE, related_name="doctor"
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="doctors",
    )

    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "doctor"

    def __str__(self):
        return self.user_profile.user.get_full_name()
