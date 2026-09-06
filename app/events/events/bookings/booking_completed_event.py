from sqlalchemy import inspect as sa_inspect

from app.core.events import DomainEvent
from app.models.booking_model import Booking


class BookingCompletedEvent(DomainEvent):
    """
    Fired when a booking transitions to CONFIRMED + PAID status.
    The handler will generate the PDF invoice and send the order confirmation email.
    """

    def __init__(self, booking: Booking) -> None:
        insp = sa_inspect(booking)

        # Safely access relationships only if loaded to prevent MissingGreenlet
        guest = booking.guest if "guest" not in insp.unloaded else None
        prop = booking.property if "property" not in insp.unloaded else None
        room_type = booking.room_type if "room_type" not in insp.unloaded else None

        guest_id = booking.guest_id
        guest_email = None
        guest_name = "Guest"
        guest_phone = None
        if guest and "email" not in sa_inspect(guest).unloaded:
            guest_email = guest.email
        if guest and "full_name" not in sa_inspect(guest).unloaded:
            guest_name = guest.full_name or "Guest"
        if guest and "phone" not in sa_inspect(guest).unloaded:
            guest_phone = getattr(guest, "phone", None)

        prop_name = "Homestay"
        prop_address = None
        if prop and "name" not in sa_inspect(prop).unloaded:
            prop_name = prop.name
        if prop and "address" not in sa_inspect(prop).unloaded:
            prop_address = prop.address

        room_type_name = None
        if room_type and "name" not in sa_inspect(room_type).unloaded:
            room_type_name = room_type.name

        payload = {
            "booking_id": int(booking.id),
            "public_id": str(booking.public_id),
            "booking_reference": booking.booking_reference,
            "invoice_number": booking.invoice_number,
            # Guest info
            "guest_id": int(guest_id),
            "guest_email": guest_email,
            "guest_name": guest_name,
            "guest_phone": guest_phone,
            # Property info
            "property_name": prop_name,
            "property_address": prop_address,
            "room_type_name": room_type_name,
            # Stay details
            "check_in_date": str(booking.check_in_date),
            "check_out_date": str(booking.check_out_date),
            "num_guests": booking.num_guests,
            "num_rooms": booking.num_rooms,
            "special_requests": booking.special_requests,
            # Pricing & Status
            "price_per_night": float(booking.price_per_night),
            "discount_amount": float(booking.discount_amount or 0),
            "tax_amount": float(booking.tax_amount or 0),
            "total_amount": float(booking.total_amount),
            "currency": booking.currency or "INR",
            "payment_status": str(booking.payment_status.value if hasattr(booking.payment_status, "value") else booking.payment_status or "paid").upper(),
        }
        super().__init__(name="booking.completed", payload=payload)

