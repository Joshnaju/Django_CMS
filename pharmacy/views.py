from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from medicine_master.models import Medicine

from .models import (MedicineInventory,PharmacyBill,PharmacyBillItem)
from .serializers import (MedicineInventorySerializer,PharmacistPrescriptionSerializer,PharmacyBillSerializer)
from .permissions import IsPharmacist

from doctor.models import MedicinePrescription
from django.db.models import Q
from django.db import transaction
from decimal import Decimal


class MedicineInventoryViewSet(viewsets.ModelViewSet):

    queryset = MedicineInventory.objects.select_related(
        "medicine"
    )

    serializer_class = MedicineInventorySerializer

    permission_classes = [IsAuthenticated,IsPharmacist]

    http_method_names = [
        "get",
        "post",
        "put",
        "patch",
        "head",
        "options",
    ]


@api_view(["GET", "PUT", "PATCH"])
@permission_classes([IsAuthenticated,IsPharmacist])
def medicine_details(request, medicine_id):

    try:
        medicine = Medicine.objects.get(id=medicine_id)

    except Medicine.DoesNotExist:
        return Response(
            {
                "detail": "Medicine not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    inventory = MedicineInventory.objects.filter(
        medicine=medicine
    ).first()

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
            data["inventory"] = MedicineInventorySerializer(
                inventory
            ).data
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

            setattr(
                medicine,
                field,
                request.data[field]
            )

    medicine.save()

    # ---------------- INVENTORY FIELDS ----------------

    inventory_fields = [
        "stock",
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
                inventory,
                data=inventory_data,
                partial=True
            )

            serializer.is_valid(
                raise_exception=True
            )

            serializer.save()

    # ---------------- CREATE NEW INVENTORY ----------------

    else:

        if inventory_data:

            required_fields = [
                "stock",
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
                        "detail":
                        "All inventory fields are required when creating inventory.",

                        "missing_fields":
                        missing_fields
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = MedicineInventorySerializer(
                data=inventory_data
            )

            serializer.is_valid(
                raise_exception=True
            )

            serializer.save(
                medicine=medicine
            )

    return Response({
        "message": "Medicine details updated successfully.",
        "medicine_id": medicine.id
    })

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
            ) |
            Q(
                consultation__appointment__doctor__user_profile__user__username__icontains=doctor_name
            )
        )

    serializer = PharmacistPrescriptionSerializer(
        prescriptions,
        many=True
    )

    return Response(serializer.data)

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsPharmacist])
def create_pharmacy_bill(request):

    patient_id = request.data.get("patient")
    items = request.data.get("items", [])

    # ---------------- PATIENT VALIDATION ----------------

    if not patient_id:
        return Response(
            {
                "detail": "Patient is required."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    if not items:
        return Response(
            {
                "detail": "At least one medicine item is required."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # ---------------- GET PRESCRIPTIONS ----------------

    bill_items_data = []
    total_amount = Decimal("0.00")

    for item in items:

        prescription_id = item.get("prescription")
        quantity = item.get("quantity")

        if not prescription_id or not quantity:

            return Response(
                {
                    "detail":
                    "Prescription and quantity are required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            prescription = MedicinePrescription.objects.select_related(
                "medicine",
                "consultation__appointment__patient"
            ).get(
                id=prescription_id
            )

        except MedicinePrescription.DoesNotExist:

            return Response(
                {
                    "detail":
                    f"Prescription {prescription_id} not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Check prescription belongs to patient

        if prescription.consultation.appointment.patient.id != patient_id:

            return Response(
                {
                    "detail":
                    "Prescription does not belong to the selected patient."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        medicine = prescription.medicine

        # ---------------- CHECK INVENTORY ----------------

        inventory = MedicineInventory.objects.filter(
            medicine=medicine
        ).first()

        if not inventory:

            return Response(
                {
                    "detail":
                    f"{medicine.name} is not available in inventory."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check stock

        if inventory.stock < quantity:

            return Response(
                {
                    "detail":
                    f"Insufficient stock for {medicine.name}.",

                    "available_stock":
                    inventory.stock
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ---------------- CALCULATE PRICE ----------------

        unit_price = medicine.price

        item_total = unit_price * quantity

        total_amount += item_total

        bill_items_data.append({
            "prescription": prescription,
            "medicine": medicine,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_price": item_total,
        })

    # ---------------- CREATE BILL ----------------

    from receptionist.models import Patient

    try:

        patient = Patient.objects.get(
            id=patient_id
        )

    except Patient.DoesNotExist:

        return Response(
            {
                "detail": "Patient not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    bill = PharmacyBill.objects.create(
        patient=patient,
        total_amount=total_amount,
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
            total_price=item_data["total_price"]
        )

    # ---------------- RESPONSE ----------------

    serializer = PharmacyBillSerializer(bill)

    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED
    )

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsPharmacist])
def pay_pharmacy_bill(request, bill_id):

    with transaction.atomic():

        # Get the bill safely
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

        # Check whether already paid

        if bill.payment_status == "PAID":

            return Response(
                {
                    "detail": "This bill has already been paid."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get all bill items

        bill_items = bill.items.select_related(
            "medicine"
        ).all()

        # ---------------- CHECK STOCK ----------------

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

        bill.save(
            update_fields=["payment_status"]
        )

        # ---------------- RESPONSE ----------------

        serializer = PharmacyBillSerializer(bill)

        return Response({
            "message":
            "Payment successful. Medicines dispensed.",

            "bill":
            serializer.data
        })