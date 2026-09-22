from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import func, or_, select

from app.models.agreement_template_model import AgreementTemplate, AgreementTemplateStatus
from app.repositories.base_repository import BaseRepository, Page


class AgreementTemplateRepository(BaseRepository[AgreementTemplate]):

    async def create(
        self,
        template: AgreementTemplate,
        commit: bool = True,
    ) -> AgreementTemplate:
        self.db.add(template)
        if commit:
            await self.db.commit()
            await self.db.refresh(template)
        else:
            await self.db.flush()
        return template

    async def get_by_id(self, template_id: int) -> Optional[AgreementTemplate]:
        query = select(AgreementTemplate).where(AgreementTemplate.id == template_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_public_id(self, public_id: UUID | str) -> Optional[AgreementTemplate]:
        pid = UUID(str(public_id)) if not isinstance(public_id, UUID) else public_id
        query = select(AgreementTemplate).where(AgreementTemplate.public_id == pid)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_default(self) -> Optional[AgreementTemplate]:
        """Return the active default template, if any."""
        query = select(AgreementTemplate).where(
            AgreementTemplate.is_default.is_(True),
            AgreementTemplate.status == AgreementTemplateStatus.ACTIVE,
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def unset_all_defaults(self) -> None:
        """Unset is_default on every template before setting a new one."""
        from sqlalchemy import update
        stmt = (
            update(AgreementTemplate)
            .where(AgreementTemplate.is_default.is_(True))
            .values(is_default=False)
            .execution_options(synchronize_session="fetch")
        )
        await self.db.execute(stmt)

    async def list_templates(
        self,
        page: int = 1,
        size: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Page[AgreementTemplate]:
        query = select(AgreementTemplate)

        if status:
            try:
                status_enum = AgreementTemplateStatus(status.lower())
                query = query.where(AgreementTemplate.status == status_enum)
            except ValueError:
                pass
        else:
            # Exclude archived by default unless explicitly requested
            query = query.where(AgreementTemplate.status != AgreementTemplateStatus.ARCHIVED)

        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    AgreementTemplate.name.ilike(term),
                    AgreementTemplate.description.ilike(term),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        sort_col = getattr(AgreementTemplate, sort_by, AgreementTemplate.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        # Always surface the default template first
        query = query.order_by(AgreementTemplate.is_default.desc(), sort_col.desc())

        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return Page(items=items, total=total, page=page, page_size=size)

    async def update(
        self,
        template: AgreementTemplate,
        commit: bool = True,
    ) -> AgreementTemplate:
        self.db.add(template)
        if commit:
            await self.db.commit()
            await self.db.refresh(template)
        else:
            await self.db.flush()
        return template

    async def delete(
        self,
        template: AgreementTemplate,
        commit: bool = True,
    ) -> None:
        await self.db.delete(template)
        if commit:
            await self.db.commit()
        else:
            await self.db.flush()

