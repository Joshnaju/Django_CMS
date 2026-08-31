from django.db import models


class Medicine(models.Model):
    name = models.CharField(max_length=150, unique=True)

    generic_name = models.CharField(max_length=150, blank=True, null=True)

    dosage_form = models.CharField(max_length=50, blank=True, null=True)

    strength = models.CharField(max_length=50, blank=True, null=True)

    manufacturer = models.CharField(max_length=150, blank=True, null=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "medicine"
        ordering = ["name"]

    def __str__(self):
        return self.name
