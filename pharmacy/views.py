from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from medicine_master.models import Medicine

from .models import MedicineInventory
from .serializers import MedicineInventorySerializer


class MedicineInventoryViewSet(viewsets.ModelViewSet):

    queryset = MedicineInventory.objects.select_related(
        "medicine"
    )

    serializer_class = MedicineInventorySerializer

    permission_classes = [AllowAny]

    http_method_names = [
        "get",
        "post",
        "put",
        "patch",
        "head",
        "options",
    ]


@api_view(["GET", "PUT", "PATCH"])
@permission_classes([AllowAny])
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

    # GET → View medicine details
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

    # PUT / PATCH → Update details

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

    inventory_fields = [
    "stock",
    "batch_number",
    "manufacturing_date",
    "expiry_date",
    "number_of_units",
]


    # If inventory already exists, update it
    if inventory:

        for field in inventory_fields:

            if field in request.data:
                setattr(
                    inventory,
                    field,
                    request.data[field]
                )

        inventory.save()


    # If inventory does not exist, create it
    else:

        inventory_data = {}

        for field in inventory_fields:

            if field in request.data:
                inventory_data[field] = request.data[field]

    # Create inventory only if pharmacy details are sent
    if inventory_data:

        MedicineInventory.objects.create(
            medicine=medicine,
            **inventory_data
        )

    return Response({
        "message": "Medicine details updated successfully.",
        "medicine_id": medicine.id
    })