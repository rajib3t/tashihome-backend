from app.core.events import DomainEvent
from app.models.booking_model import Booking


class BookingCompletedEvent(DomainEvent):
    """
    Fired when a booking transitions to CONFIRMED + PAID status.
    The handler will generate the PDF invoice and send the order confirmation email.
    """

    def __init__(self, booking: Booking) -> None:
        guest = booking.guest
        prop = booking.property

        payload = {
            "booking_id": int(booking.id),
            "public_id": str(booking.public_id),
            "booking_reference": booking.booking_reference,
            "invoice_number": booking.invoice_number,
            # Guest info
            "guest_id": int(booking.guest_id),
            "guest_email": guest.email if guest else None,
            "guest_name": guest.full_name if guest else "Guest",
            # Property info
            "property_name": prop.name if prop else "N/A",
            "property_address": prop.address if prop else None,
            # Stay details
            "check_in_date": str(booking.check_in_date),
            "check_out_date": str(booking.check_out_date),
            "num_guests": booking.num_guests,
            "num_rooms": booking.num_rooms,
            # Pricing
            "price_per_night": float(booking.price_per_night),
            "discount_amount": float(booking.discount_amount or 0),
            "tax_amount": float(booking.tax_amount or 0),
            "total_amount": float(booking.total_amount),
            "currency": booking.currency or "INR",
        }
        super().__init__(name="booking.completed", payload=payload)
