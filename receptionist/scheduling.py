from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone

from .models import Appointment


CONSULTATION_DURATION = 15

WORK_START = time(9, 0)
WORK_END = time(18, 0)

INDIA_TIMEZONE = ZoneInfo("Asia/Kolkata")

BREAK_PERIODS = [
    (time(11, 0), time(11, 15)),  # Morning break
    (time(13, 0), time(14, 0)),   # Lunch break
    (time(16, 0), time(16, 15)),  # Evening break
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
):
    all_slots = generate_all_slots()

    booked_slots = set(
        Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
        )
        .exclude(
            status="CANCELLED"
        )
        .values_list(
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

    # For today's walk-in appointments,
    # remove all time slots that have already passed.
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
):
    available_slots = get_available_slots(
        doctor,
        appointment_date,
    )

    if not available_slots:
        return None

    return available_slots[0]


def is_valid_appointment_slot(
    doctor,
    appointment_date,
    appointment_time,
):
    next_slot = get_next_available_slot(
        doctor,
        appointment_date,
    )

    if next_slot is None:
        return False

    return appointment_time == next_slot


