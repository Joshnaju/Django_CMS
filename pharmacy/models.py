from django.db import models
from medicine_master.models import Medicine


class MedicineInventory(models.Model):

    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE,
        related_name="inventory"
    )

    stock = models.PositiveIntegerField(default=0)

    batch_number = models.CharField(
        max_length=100
    )

    manufacturing_date = models.DateField()

    expiry_date = models.DateField()

    number_of_units = models.PositiveIntegerField()

    class Meta:
        db_table = "medicine_inventory"

    def __str__(self):
        return f"{self.medicine.name} - {self.batch_number}"