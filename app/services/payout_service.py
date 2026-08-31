from datetime import date
from typing import Any, Dict, List, Optional

from app.models.payout_model import Payout
from app.repositories.base_repository import Page
from app.repositories.payout_repository import PayoutRepository, PayoutWithRelations


class PayoutService:
    def __init__(self, repository: PayoutRepository):
        self.repository = repository

    async def create(
        self,
        payout: Payout,
        with_relations: Optional[PayoutWithRelations] = None,
        commit: bool = True,
    ) -> Payout:
        return await self.repository.create(payout, with_relations=with_relations, commit=commit)

    async def get_by_id(
        self,
        payout_id: int,
        with_relations: Optional[PayoutWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Payout]:
        return await self.repository.get_by_id(payout_id, with_relations=with_relations, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[PayoutWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Payout]:
        return await self.repository.get_by_public_id(public_id, with_relations=with_relations, flush=flush)

    async def get_by_razorpay_payout_id(
        self,
        razorpay_payout_id: str,
        with_relations: Optional[PayoutWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Payout]:
        return await self.repository.get_by_razorpay_payout_id(
            razorpay_payout_id, with_relations=with_relations, flush=flush
        )

    async def update(
        self,
        payout: Payout,
        with_relations: Optional[PayoutWithRelations] = None,
        commit: bool = True,
    ) -> Payout:
        return await self.repository.update(payout, with_relations=with_relations, commit=commit)

    async def list_all(
        self,
        page: int = 1,
        page_size: int = 10,
        vendor_id: Optional[int] = None,
        status: Optional[str] = None,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        sort_order: str = "desc",
        with_relations: Optional[PayoutWithRelations] = None,
        flush: bool = False,
    ) -> Page[Payout]:
        return await self.repository.list_all(
            page=page,
            page_size=page_size,
            vendor_id=vendor_id,
            status=status,
            period_start=period_start,
            period_end=period_end,
            sort_order=sort_order,
            with_relations=with_relations,
            flush=flush,
        )

    async def calculate_vendor_earnings(
        self,
        vendor_id: int,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        commission_percentage: float = 10.0,
    ) -> Dict[str, Any]:
        return await self.repository.calculate_vendor_earnings_summary(
            vendor_id=vendor_id,
            period_start=period_start,
            period_end=period_end,
            commission_percentage=commission_percentage,
        )

