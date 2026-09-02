from django.db import models
from medicine_master.models import Medicine
from receptionist.models import Patient
from doctor.models import MedicinePrescription


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


# ==============================
# PHARMACY BILL
# ==============================

class PharmacyBill(models.Model):

    PAYMENT_STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="pharmacy_bills"
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="PENDING"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "pharmacy_bill"

    def __str__(self):
        return f"Pharmacy Bill {self.id} - {self.patient.patient_name}"


# ==============================
# PHARMACY BILL ITEM
# ==============================

class PharmacyBillItem(models.Model):

    pharmacy_bill = models.ForeignKey(
        PharmacyBill,
        on_delete=models.CASCADE,
        related_name="items"
    )

    prescription = models.ForeignKey(
        MedicinePrescription,
        on_delete=models.PROTECT,
        related_name="bill_items"
    )

    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.PROTECT
    )

    quantity = models.PositiveIntegerField()

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        db_table = "pharmacy_bill_item"

    def __str__(self):
        return (
            f"{self.medicine.name} - "
            f"Bill {self.pharmacy_bill.id}"
        )