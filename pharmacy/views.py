from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum, F
from datetime import timedelta

from medicine_master.models import Medicine

from .models import MedicineInventory, PharmacyBill, PharmacyBillItem
from .serializers import (
    MedicineInventorySerializer,
    PharmacistPrescriptionSerializer,
    PharmacyBillSerializer,
)
from .permissions import IsPharmacist

from doctor.models import MedicinePrescription
from django.db.models import Q
from django.db import transaction
from decimal import Decimal


class MedicineInventoryViewSet(viewsets.ModelViewSet):

    queryset = MedicineInventory.objects.select_related("medicine")

    serializer_class = MedicineInventorySerializer

    permission_classes = [IsAuthenticated, IsPharmacist]

    http_method_names = [
        "get",
        "post",
        "put",
        "patch",
        "head",
        "options",
    ]


@api_view(["GET", "PUT", "PATCH"])
@permission_classes([IsAuthenticated, IsPharmacist])
def medicine_details(request, medicine_id):

    try:
        medicine = Medicine.objects.get(id=medicine_id)

    except Medicine.DoesNotExist:
        return Response(
            {"detail": "Medicine not found."}, status=status.HTTP_404_NOT_FOUND
        )

    inventory = MedicineInventory.objects.filter(medicine=medicine).first()

    # ---------------- GET ----------------
    if request.method == "GET":

        data = {
            "medicine_id": medicine.id,
            "name": medicine.name,
            "generic_name": medicine.generic_name,
            "dosage_form": medicine.dosage_form,
            "strength": medicine.strength,
            "manufacturer": medicine.manufacturer,
            "price": medicine.price,
        }

        if inventory:
            data["inventory"] = MedicineInventorySerializer(inventory).data
        else:
            data["inventory"] = None

        return Response(data)

    # ---------------- UPDATE MEDICINE ----------------

    medicine_fields = [
        "name",
        "generic_name",
        "dosage_form",
        "strength",
        "manufacturer",
        "price",
    ]

    for field in medicine_fields:

        if field in request.data:

            setattr(medicine, field, request.data[field])

    medicine.save()

    # ---------------- INVENTORY FIELDS ----------------

    inventory_fields = [
        "stock",
        "min_stock",
        "max_stock",
        "batch_number",
        "manufacturing_date",
        "expiry_date",
        "number_of_units",
    ]

    inventory_data = {}

    for field in inventory_fields:

        if field in request.data:

            inventory_data[field] = request.data[field]

    # ---------------- UPDATE EXISTING INVENTORY ----------------

    if inventory:

        if inventory_data:

            serializer = MedicineInventorySerializer(
                inventory, data=inventory_data, partial=True
            )

            serializer.is_valid(raise_exception=True)

            serializer.save()

    # ---------------- CREATE NEW INVENTORY ----------------

    else:

        if inventory_data:

            required_fields = [
                "stock",
                "min_stock",
                "max_stock",
                "batch_number",
                "manufacturing_date",
                "expiry_date",
                "number_of_units",
            ]

            missing_fields = []

            for field in required_fields:

                if field not in inventory_data:

                    missing_fields.append(field)

            if missing_fields:

                return Response(
                    {
                        "detail": "All inventory fields are required when creating inventory.",
                        "missing_fields": missing_fields,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = MedicineInventorySerializer(data=inventory_data)

            serializer.is_valid(raise_exception=True)

            serializer.save(medicine=medicine)

    return Response(
        {
            "message": "Medicine details updated successfully.",
            "medicine_id": medicine.id,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsPharmacist])
def prescription_search(request):

    patient_id = request.query_params.get("patient_id")
    patient_name = request.query_params.get("patient_name")
    doctor_name = request.query_params.get("doctor_name")

    prescriptions = MedicinePrescription.objects.select_related(
        "medicine",
        "consultation",
        "consultation__appointment",
        "consultation__appointment__patient",
        "consultation__appointment__doctor",
        "consultation__appointment__doctor__user_profile",
        "consultation__appointment__doctor__user_profile__user",
    )

    if patient_id:
        prescriptions = prescriptions.filter(
            consultation__appointment__patient__patient_id__icontains=patient_id
        )

    if patient_name:
        prescriptions = prescriptions.filter(
            consultation__appointment__patient__patient_name__icontains=patient_name
        )

    if doctor_name:
        prescriptions = prescriptions.filter(
            Q(
                consultation__appointment__doctor__user_profile__name__icontains=doctor_name
            )
            | Q(
                consultation__appointment__doctor__user_profile__user__username__icontains=doctor_name
            )
        )

    serializer = PharmacistPrescriptionSerializer(prescriptions, many=True)

    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsPharmacist])
def create_pharmacy_bill(request):

    patient_id = request.data.get("patient")
    items = request.data.get("items", [])

    # ---------------- PATIENT ID VALIDATION ----------------

    if not patient_id:

        return Response(
            {
                "detail": "Patient is required."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:

        patient_id = int(patient_id)

    except (ValueError, TypeError):

        return Response(
            {
                "detail":
                "Patient ID must be a valid number."
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
     # ---------------- ITEMS VALIDATION ----------------

    if not items:

        return Response(
            {
                "detail":
                "At least one medicine item is required."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # ---------------- GET PRESCRIPTIONS ----------------

    bill_items_data = []
    subtotal = Decimal("0.00")

    used_prescription_ids = set()

    for item in items:

        prescription_id = item.get("prescription")
        quantity = item.get("quantity")

        # ---------------- REQUIRED VALIDATION ----------------

        if not prescription_id or quantity is None:

            return Response(
                {
                    "detail":
                    "Prescription and quantity are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------- DUPLICATE PRESCRIPTION VALIDATION ----------------

        if prescription_id in used_prescription_ids:

            return Response(
                {
                    "detail":
                    f"Prescription {prescription_id} has been added more than once."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        used_prescription_ids.add(prescription_id)

        # ---------------- QUANTITY NUMBER VALIDATION ----------------

        try:

            quantity = int(quantity)

        except (ValueError, TypeError):

            return Response(
                {
                    "detail":
                    "Quantity must be a valid number."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------- QUANTITY POSITIVE VALIDATION ----------------

        if quantity <= 0:

            return Response(
                {
                    "detail":
                    "Quantity must be greater than zero."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            prescription = MedicinePrescription.objects.select_related(
                "medicine",
                "consultation__appointment__patient"
            ).get(id=prescription_id)

        except MedicinePrescription.DoesNotExist:

            return Response(
                {
                    "detail":
                    f"Prescription {prescription_id} not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check prescription belongs to patient

        if prescription.consultation.appointment.patient.id != patient_id:

            return Response(
                {"detail": "Prescription does not belong to the selected patient."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        medicine = prescription.medicine

        # ---------------- MEDICINE VALIDATION ----------------

        if not medicine:

            return Response(
                {
                    "detail":
                    f"Prescription {prescription_id} does not have a valid medicine."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------- CHECK INVENTORY ----------------

        inventory = MedicineInventory.objects.filter(medicine=medicine).first()

        if not inventory:

            return Response(
                {"detail": f"{medicine.name} is not available in inventory."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check stock

        if inventory.stock < quantity:

            return Response(
                {
                    "detail": f"Insufficient stock for {medicine.name}.",
                    "available_stock": inventory.stock,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------- CALCULATE PRICE ----------------

        unit_price = medicine.price

        item_total = unit_price * quantity

        subtotal += item_total

        bill_items_data.append(
            {
                "prescription": prescription,
                "medicine": medicine,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_price": item_total,
            }
        )
    # ---------------- GST CALCULATION ----------------

    gst_amount = (
        subtotal * Decimal("0.05")
    ).quantize(
        Decimal("0.01")
    )

    # ---------------- GRAND TOTAL ----------------

    total_amount = (
        subtotal + gst_amount
    ).quantize(
        Decimal("0.01")
    )

    # ---------------- CREATE BILL ----------------

    from receptionist.models import Patient

    try:

        patient = Patient.objects.get(id=patient_id)

    except Patient.DoesNotExist:

        return Response(
            {"detail": "Patient not found."}, status=status.HTTP_404_NOT_FOUND
        )

    bill = PharmacyBill.objects.create(
    patient=patient,
    subtotal=subtotal,
    gst_amount=gst_amount,
    total_amount=total_amount,
    amount_paid=Decimal("0.00"),
    payment_status="PENDING"
    )

    # ---------------- CREATE BILL ITEMS ----------------

    for item_data in bill_items_data:

        PharmacyBillItem.objects.create(
            pharmacy_bill=bill,
            prescription=item_data["prescription"],
            medicine=item_data["medicine"],
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            total_price=item_data["total_price"],
        )

    # ---------------- RESPONSE ----------------

    serializer = PharmacyBillSerializer(bill)

    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsPharmacist])
def pay_pharmacy_bill(request, bill_id):

    with transaction.atomic():

        # ---------------- GET BILL ----------------

        try:

            bill = PharmacyBill.objects.select_for_update().get(
                id=bill_id
            )

        except PharmacyBill.DoesNotExist:

            return Response(
                {
                    "detail": "Pharmacy bill not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # ---------------- CHECK PAYMENT STATUS ----------------

        if bill.payment_status == "PAID":

            return Response(
                {
                    "detail": "This bill has already been paid."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ---------------- GET BILL ITEMS ----------------

        bill_items = bill.items.select_related(
            "medicine"
        ).all()

        today = timezone.now().date()

        # ---------------- CHECK STOCK AND EXPIRY ----------------

        for item in bill_items:

            try:

                inventory = MedicineInventory.objects.select_for_update().get(
                    medicine=item.medicine
                )

            except MedicineInventory.DoesNotExist:

                return Response(
                    {
                        "detail":
                        f"Inventory not found for {item.medicine.name}."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check expiry

            if inventory.expiry_date < today:

                return Response(
                    {
                        "detail":
                        f"{item.medicine.name} has expired.",

                        "expiry_date":
                        inventory.expiry_date
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check stock

            if inventory.stock < item.quantity:

                return Response(
                    {
                        "detail":
                        f"Insufficient stock for {item.medicine.name}.",

                        "available_stock":
                        inventory.stock,

                        "required_quantity":
                        item.quantity
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        # ---------------- REDUCE STOCK ----------------

        for item in bill_items:

            inventory = MedicineInventory.objects.select_for_update().get(
                medicine=item.medicine
            )

            inventory.stock -= item.quantity

            inventory.save(
                update_fields=["stock"]
            )

        # ---------------- MARK BILL AS PAID ----------------

        bill.payment_status = "PAID"

        # Amount paid should equal the final bill amount
        bill.amount_paid = bill.total_amount

        bill.save(
            update_fields=[
                "payment_status",
                "amount_paid"
            ]
        )

        # ---------------- RESPONSE ----------------

        serializer = PharmacyBillSerializer(bill)

        return Response(
            {
                "message":
                "Payment successful. Medicines dispensed.",

                "bill":
                serializer.data
            }
        )

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsPharmacist])
def pharmacy_sales_report(request):

    period = request.query_params.get("period", "daily")
    period = "custom"
    date_param = request.query_params.get("date")

    start_date_param = request.query_params.get("start_date")
    end_date_param = request.query_params.get("end_date")

    today = timezone.now().date()

    # =====================================
    # SPECIFIC DATE
    # =====================================

    if date_param:

        try:

            selected_date = timezone.datetime.strptime(
                date_param,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            return Response(
                {
                    "detail":
                    "Invalid date format. Use YYYY-MM-DD."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        start_date = selected_date
        end_date = selected_date

    # =====================================
    # SPECIFIC WEEK / DATE RANGE
    # =====================================

    elif start_date_param and end_date_param:

        period = "custom"

        try:

            start_date = timezone.datetime.strptime(
                start_date_param,
                "%Y-%m-%d"
            ).date()

            end_date = timezone.datetime.strptime(
                end_date_param,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            return Response(
                {
                    "detail":
                    "Invalid date format. Use YYYY-MM-DD."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if start_date > end_date:

            return Response(
                {
                    "detail":
                    "Start date cannot be greater than end date."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


    # =====================================
    # DAILY
    # =====================================

    elif period == "daily":

        start_date = today
        end_date = today

    # =====================================
    # CURRENT WEEK
    # =====================================

    elif period == "weekly":

        start_date = today - timedelta(days=6)
        end_date = today

    # =====================================
    # MONTHLY
    # =====================================

    elif period == "monthly":

        start_date = today.replace(day=1)
        end_date = today

    else:

        return Response(
            {
                "detail":
                "Invalid period. Use daily, weekly, monthly or provide a date."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # =====================================
    # GET PAID BILLS
    # =====================================

    paid_bills = PharmacyBill.objects.filter(
        payment_status="PAID",
        created_at__date__range=[
            start_date,
            end_date
        ]
    ).prefetch_related(
        "items",
        "items__medicine"
    ).select_related(
        "patient"
    )

    # =====================================
    # TOTAL SALES
    # =====================================

    total_sales = paid_bills.aggregate(
        total=Sum("total_amount")
    )["total"] or Decimal("0.00")

    # =====================================
    # TOTAL ITEMS SOLD
    # =====================================

    total_items_sold = 0

    records = []

    # =====================================
    # CREATE RECORDS
    # =====================================

    for bill in paid_bills:

        for item in bill.items.all():

            total_items_sold += item.quantity

            records.append(
                {
                    "dispensing_id": item.id,

                    "bill_number":
                    f"PHARM-{bill.id:06d}",

                    "medicine_id":
                    item.medicine.id,

                    "medicine":
                    item.medicine.name,

                    "patient":
                    bill.patient.patient_name,

                    "quantity":
                    item.quantity,

                    "unit_price":
                    item.unit_price,

                    "total_price":
                    item.total_price,

                    "dispensed_at":
                    bill.created_at,
                }
            )

    # =====================================
    # RESPONSE
    # =====================================

    return Response(
        {
            "period": period,

            "start_date":
            start_date,

            "end_date":
            end_date,

            "total_sales":
            total_sales,

            "total_items_sold":
            total_items_sold,

            "records":
            records,
        }
    )

# =====================================
# LOW STOCK / REORDER ALERT
# =====================================

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsPharmacist])
def low_stock_alert(request):

    low_stock_medicines = MedicineInventory.objects.filter(
        stock__lte=F("min_stock")
    ).select_related(
        "medicine"
    )

    records = []

    for inventory in low_stock_medicines:

        records.append(
            {
                "inventory_id": inventory.id,

                "medicine_id": inventory.medicine.id,

                "medicine_name": inventory.medicine.name,

                "current_stock": inventory.stock,

                "min_stock": inventory.min_stock,

                "max_stock": inventory.max_stock,

                "reorder_quantity":
                max(
                    inventory.max_stock - inventory.stock,
                    0
                ),

                "status": "LOW STOCK"
            }
        )

    return Response(
        {
            "total_low_stock_medicines":
            len(records),

            "records":
            records
        }
    )

# =====================================
# SEARCH MEDICINE
# =====================================

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsPharmacist])
def search_medicine(request):

    search = request.query_params.get("search")

    medicines = MedicineInventory.objects.select_related(
        "medicine"
    )

    # ---------------- SEARCH ----------------

    if search:

        filters = (
            Q(
                medicine__name__icontains=search
            )
            |
            Q(
                medicine__generic_name__icontains=search
            )
        )

        # ---------------- SEARCH BY MEDICINE ID ----------------

        if search.isdigit():

            filters |= Q(
                medicine__id=int(search)
            )

        medicines = medicines.filter(
            filters
        )

    serializer = MedicineInventorySerializer(
        medicines,
        many=True
    )

    return Response(serializer.data)