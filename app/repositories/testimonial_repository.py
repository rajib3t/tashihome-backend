from typing import Optional, TypedDict

from sqlalchemy import or_, select

from app.models.testimonial_model import Testimonial, TestimonialStatus
from app.models.user_model import User
from app.repositories.base_repository import BaseRepository, Page


class TestimonialWithRelations(TypedDict, total=False):
    user: bool


def _parse_testimonial_status(status: Optional[str | TestimonialStatus]) -> Optional[TestimonialStatus]:
    if not status:
        return None
    if isinstance(status, TestimonialStatus):
        return status
    try:
        return TestimonialStatus(status.lower())
    except ValueError:
        try:
            return TestimonialStatus[status.upper()]
        except KeyError:
            return None


class TestimonialRepository(BaseRepository[Testimonial]):
    _relation_map = {
        "user": Testimonial.user,
    }

    async def create(
        self,
        testimonial: Testimonial,
        with_relations: Optional[TestimonialWithRelations] = None,
        commit: bool = True,
    ) -> Testimonial:
        self.db.add(testimonial)
        if commit:
            await self.db.commit()
            await self.db.refresh(testimonial)
        if with_relations:
            query = self._apply_relations(
                select(Testimonial).where(Testimonial.id == testimonial.id),
                with_relations,
                self._relation_map,
            )
            reloaded = await self._fetch_one(query)
            if reloaded:
                return reloaded
        return testimonial

    async def get_by_id(
        self,
        testimonial_id: int,
        with_relations: Optional[TestimonialWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Testimonial]:
        query = select(Testimonial).where(Testimonial.id == testimonial_id)
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[TestimonialWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Testimonial]:
        query = select(Testimonial).where(Testimonial.public_id == public_id)
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._fetch_one(query, flush=flush)

    async def list_by_user(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
        sort_order: str = "desc",
        with_relations: Optional[TestimonialWithRelations] = None,
        flush: bool = False,
    ) -> Page[Testimonial]:
        query = select(Testimonial).where(Testimonial.user_id == user_id)
        if sort_order.lower() == "asc":
            query = query.order_by(Testimonial.created_at.asc())
        else:
            query = query.order_by(Testimonial.created_at.desc())

        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)

    async def list_public(
        self,
        is_featured: Optional[bool] = None,
        user_role: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        sort_order: str = "desc",
        with_relations: Optional[TestimonialWithRelations] = None,
        flush: bool = False,
    ) -> Page[Testimonial]:
        query = select(Testimonial).where(Testimonial.status == TestimonialStatus.APPROVED)

        if is_featured is not None:
            query = query.where(Testimonial.is_featured == is_featured)

        if user_role:
            query = query.where(Testimonial.user_role == user_role.lower())

        if sort_order.lower() == "asc":
            query = query.order_by(Testimonial.created_at.asc())
        else:
            query = query.order_by(Testimonial.created_at.desc())

        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)

    async def list_all(
        self,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str | TestimonialStatus] = None,
        user_role: Optional[str] = None,
        is_featured: Optional[bool] = None,
        search: Optional[str] = None,
        sort_order: str = "desc",
        with_relations: Optional[TestimonialWithRelations] = None,
        flush: bool = False,
    ) -> Page[Testimonial]:
        query = select(Testimonial)

        status_enum = _parse_testimonial_status(status)
        if status_enum is not None:
            query = query.where(Testimonial.status == status_enum)

        if user_role:
            query = query.where(Testimonial.user_role == user_role.lower())

        if is_featured is not None:
            query = query.where(Testimonial.is_featured == is_featured)

        if search:
            term = f"%{search.strip()}%"
            query = (
                query.outerjoin(Testimonial.user)
                .where(
                    or_(
                        Testimonial.name.ilike(term),
                        Testimonial.content.ilike(term),
                        Testimonial.designation.ilike(term),
                        User.full_name.ilike(term),
                        User.email.ilike(term),
                    )
                )
            )

        if sort_order.lower() == "asc":
            query = query.order_by(Testimonial.created_at.asc())
        else:
            query = query.order_by(Testimonial.created_at.desc())

        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)

    async def update(
        self,
        testimonial: Testimonial,
        with_relations: Optional[TestimonialWithRelations] = None,
        commit: bool = True,
    ) -> Testimonial:
        self.db.add(testimonial)
        if commit:
            await self.db.commit()
            await self.db.refresh(testimonial)
        if with_relations:
            query = self._apply_relations(
                select(Testimonial).where(Testimonial.id == testimonial.id),
                with_relations,
                self._relation_map,
            )
            reloaded = await self._fetch_one(query)
            if reloaded:
                return reloaded
        return testimonial

    async def delete(self, testimonial: Testimonial, commit: bool = True) -> None:
        await self.db.delete(testimonial)
        if commit:
            await self.db.commit()

