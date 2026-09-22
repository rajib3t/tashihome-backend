from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.application.dto.agreements.agreement_dto import AgreementQueryDTO
from app.models.company_model import Company
from app.models.user_model import User
from app.models.vendor_agreement_model import AgreementStatus, VendorAgreement
from app.repositories.base_repository import BaseRepository, Page

AGREEMENT_RELATIONS = (
    selectinload(VendorAgreement.vendor)
    .selectinload(User.company)
    .selectinload(Company.addresses),
    selectinload(VendorAgreement.vendor).selectinload(User.addresses),
    selectinload(VendorAgreement.host_request),
)


class VendorAgreementRepository(BaseRepository[VendorAgreement]):
    async def create(
        self,
        agreement: VendorAgreement,
        commit: bool = False,
    ) -> VendorAgreement:
        self.db.add(agreement)
        if commit:
            await self.db.commit()
            await self.db.refresh(agreement)
        else:
            await self.db.flush()
        return agreement

    async def get_by_id(
        self,
        agreement_id: int,
        flush: bool = False,
    ) -> Optional[VendorAgreement]:
        if flush:
            await self.db.flush()
        query = (
            select(VendorAgreement)
            .where(VendorAgreement.id == agreement_id)
            .options(*AGREEMENT_RELATIONS)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_public_id(
        self,
        public_id: UUID | str,
        flush: bool = False,
    ) -> Optional[VendorAgreement]:
        if flush:
            await self.db.flush()
        pid = UUID(str(public_id)) if not isinstance(public_id, UUID) else public_id
        query = (
            select(VendorAgreement)
            .where(VendorAgreement.public_id == pid)
            .options(*AGREEMENT_RELATIONS)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_token(
        self,
        token: str,
        flush: bool = False,
    ) -> Optional[VendorAgreement]:
        if flush:
            await self.db.flush()
        query = (
            select(VendorAgreement)
            .where(VendorAgreement.token == token)
            .options(*AGREEMENT_RELATIONS)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_latest_by_vendor_id(
        self,
        vendor_id: int,
        flush: bool = False,
    ) -> Optional[VendorAgreement]:
        if flush:
            await self.db.flush()
        query = (
            select(VendorAgreement)
            .where(VendorAgreement.vendor_id == vendor_id)
            .options(*AGREEMENT_RELATIONS)
            .order_by(VendorAgreement.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_pending_by_vendor_id(
        self,
        vendor_id: int,
        flush: bool = False,
    ) -> Optional[VendorAgreement]:
        """Return the active pending agreement for this vendor, if any (SENT, VIEWED, PARTIALLY_SIGNED)."""
        if flush:
            await self.db.flush()
        query = (
            select(VendorAgreement)
            .where(
                VendorAgreement.vendor_id == vendor_id,
                VendorAgreement.status.in_([
                    AgreementStatus.SENT,
                    AgreementStatus.VIEWED,
                    AgreementStatus.PARTIALLY_SIGNED,
                ]),
            )
            .options(*AGREEMENT_RELATIONS)
            .order_by(VendorAgreement.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_all_by_vendor_id(
        self,
        vendor_id: int,
        flush: bool = False,
    ) -> list[VendorAgreement]:
        """Return all historical and active agreements for a vendor ordered newest to oldest."""
        if flush:
            await self.db.flush()
        query = (
            select(VendorAgreement)
            .where(VendorAgreement.vendor_id == vendor_id)
            .options(*AGREEMENT_RELATIONS)
            .order_by(VendorAgreement.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())


    async def list_agreements(
        self,
        params: AgreementQueryDTO,
    ) -> Page[VendorAgreement]:
        query = select(VendorAgreement).options(*AGREEMENT_RELATIONS)

        if params.status:
            try:
                status_enum = AgreementStatus(params.status.lower())
                query = query.where(VendorAgreement.status == status_enum)
            except ValueError:
                pass

        if params.vendor_id:
            query = query.join(VendorAgreement.vendor).where(
                or_(
                    User.public_id == UUID(params.vendor_id) if len(params.vendor_id) == 36 else False,
                    VendorAgreement.vendor_id == int(params.vendor_id) if params.vendor_id.isdigit() else False,
                )
            )

        if params.search:
            search_term = f"%{params.search.strip()}%"
            query = query.join(VendorAgreement.vendor, isouter=True).where(
                or_(
                    VendorAgreement.title.ilike(search_term),
                    VendorAgreement.signer_name.ilike(search_term),
                    VendorAgreement.signer_email.ilike(search_term),
                    VendorAgreement.token.ilike(search_term),
                    User.full_name.ilike(search_term),
                    User.email.ilike(search_term),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        # Sorting
        sort_col = getattr(VendorAgreement, params.sort_by, VendorAgreement.created_at)
        if params.sort_order.lower() == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        # Pagination
        offset = (params.page - 1) * params.size
        query = query.offset(offset).limit(params.size)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return Page(
            items=items,
            total=total,
            page=params.page,
            page_size=params.size,
        )

    async def update(
        self,
        agreement: VendorAgreement,
        commit: bool = False,
    ) -> VendorAgreement:
        self.db.add(agreement)
        if commit:
            await self.db.commit()
            await self.db.refresh(agreement)
        else:
            await self.db.flush()
        return agreement

    async def delete(
        self,
        agreement: VendorAgreement,
        commit: bool = False,
    ) -> None:
        await self.db.delete(agreement)
        if commit:
            await self.db.commit()
        else:
            await self.db.flush()

