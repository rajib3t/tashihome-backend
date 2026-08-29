from typing import Optional, Sequence

from sqlalchemy import select

from app.models.payment_model import Payment, TransactionStatus
from app.repositories.base_repository import BaseRepository, Page


class PaymentRepository(BaseRepository[Payment]):
    async def create(self, payment: Payment, commit: bool = True) -> Payment:
        self.db.add(payment)
        if commit:
            await self.db.commit()
            await self.db.refresh(payment)
        return payment

    async def get_by_id(self, payment_id: int, flush: bool = False) -> Optional[Payment]:
        query = select(Payment).where(Payment.id == payment_id)
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(self, public_id: str, flush: bool = False) -> Optional[Payment]:
        query = select(Payment).where(Payment.public_id == public_id)
        return await self._fetch_one(query, flush=flush)

    async def get_by_transaction_id(self, transaction_id: str, flush: bool = False) -> Optional[Payment]:
        query = select(Payment).where(Payment.transaction_id == transaction_id)
        return await self._fetch_one(query, flush=flush)

    async def list_by_booking_id(self, booking_id: int, flush: bool = False) -> list[Payment]:
        query = (
            select(Payment)
            .where(Payment.booking_id == booking_id)
            .order_by(Payment.created_at.desc())
        )
        return await self._fetch_all(query, flush=flush)

    async def update(self, payment: Payment, commit: bool = True) -> Payment:
        self.db.add(payment)
        if commit:
            await self.db.commit()
            await self.db.refresh(payment)
        return payment

