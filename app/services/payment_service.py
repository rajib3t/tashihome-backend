from typing import Optional

from app.models.payment_model import Payment
from app.repositories.payment_repository import PaymentRepository


class PaymentService:
    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository

    async def create(self, payment: Payment, commit: bool = True) -> Payment:
        return await self.payment_repository.create(payment, commit=commit)

    async def get_by_id(self, payment_id: int, flush: bool = False) -> Optional[Payment]:
        return await self.payment_repository.get_by_id(payment_id, flush=flush)

    async def get_by_public_id(self, public_id: str, flush: bool = False) -> Optional[Payment]:
        return await self.payment_repository.get_by_public_id(public_id, flush=flush)

    async def get_by_transaction_id(self, transaction_id: str, flush: bool = False) -> Optional[Payment]:
        return await self.payment_repository.get_by_transaction_id(transaction_id, flush=flush)

    async def list_by_booking_id(self, booking_id: int, flush: bool = False) -> list[Payment]:
        return await self.payment_repository.list_by_booking_id(booking_id, flush=flush)

    async def update(self, payment: Payment, commit: bool = True) -> Payment:
        return await self.payment_repository.update(payment, commit=commit)

