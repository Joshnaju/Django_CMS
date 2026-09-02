from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from medicine_master.models import Medicine

from .models import MedicineInventory
from .serializers import MedicineInventorySerializer
from .permissions import IsPharmacist


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