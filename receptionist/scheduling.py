from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone

from .models import Appointment


CONSULTATION_DURATION = 15

WORK_START = time(9, 0)
WORK_END = time(18, 0)

INDIA_TIMEZONE = ZoneInfo("Asia/Kolkata")

BREAK_PERIODS = [
    (time(11, 0), time(11, 15)),
    (time(13, 0), time(14, 0)),
    (time(16, 0), time(16, 15)),
]


def get_india_now():
    return timezone.now().astimezone(
        INDIA_TIMEZONE
    )


def generate_all_slots():
    slots = []

    today = get_india_now().date()

    current = datetime.combine(
        today,
        WORK_START,
    )

    end = datetime.combine(
        today,
        WORK_END,
    )

    while current < end:
        slot_time = current.time()

        is_break = any(
            break_start <= slot_time < break_end
            for break_start, break_end in BREAK_PERIODS
        )

        if not is_break:
            slots.append(slot_time)

        current += timedelta(
            minutes=CONSULTATION_DURATION
        )

    return slots


def get_available_slots(
    doctor,
    appointment_date,
    exclude_appointment=None,
):
    all_slots = generate_all_slots()

    booked_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=appointment_date,
    ).exclude(
        status="CANCELLED"
    )

    # Used while editing an existing appointment.
    # The appointment's own current slot must not block itself.
    if exclude_appointment is not None:
        booked_appointments = booked_appointments.exclude(
            pk=exclude_appointment.pk
        )

    booked_slots = set(
        booked_appointments.values_list(
            "appointment_time",
            flat=True,
        )
    )

    available_slots = [
        slot
        for slot in all_slots
        if slot not in booked_slots
    ]

    india_now = get_india_now()
    india_today = india_now.date()

    # Remove already-passed slots for today's appointments.
    if appointment_date == india_today:
        current_time = india_now.time()

        available_slots = [
            slot
            for slot in available_slots
            if slot > current_time
        ]

    return available_slots


def get_next_available_slot(
    doctor,
    appointment_date,
    exclude_appointment=None,
):
    available_slots = get_available_slots(
        doctor,
        appointment_date,
        exclude_appointment=exclude_appointment,
    )

    if not available_slots:
        return None

    return available_slots[0]


def is_next_available_slot(
    doctor,
    appointment_date,
    appointment_time,
    exclude_appointment=None,
):
    """
    Used for WALK_IN appointments.

    Walk-in appointments must always use the next available
    appointment slot.
    """

    next_slot = get_next_available_slot(
        doctor,
        appointment_date,
        exclude_appointment=exclude_appointment,
    )

    if next_slot is None:
        return False

    return appointment_time == next_slot


def is_available_slot(
    doctor,
    appointment_date,
    appointment_time,
    exclude_appointment=None,
):
    """
    Used for PRIOR_BOOKING appointments and appointment editing.

    The selected time may be any currently available valid slot.
    """

    available_slots = get_available_slots(
        doctor,
        appointment_date,
        exclude_appointment=exclude_appointment,
    )

    return appointment_time in available_slots


# Kept for compatibility with any existing receptionist code
# that may still import this function.
def is_valid_appointment_slot(
    doctor,
    appointment_date,
    appointment_time,
):
    return is_next_available_slot(
        doctor,
        appointment_date,
        appointment_time,
    )