from typing import Optional

from app.models.testimonial_model import Testimonial
from app.repositories.base_repository import Page
from app.repositories.testimonial_repository import (
    TestimonialRepository,
    TestimonialWithRelations,
)


class TestimonialService:
    def __init__(self, testimonial_repository: TestimonialRepository):
        self.testimonial_repository = testimonial_repository

    async def create(
        self,
        testimonial: Testimonial,
        with_relations: Optional[TestimonialWithRelations] = None,
        commit: bool = True,
    ) -> Testimonial:
        return await self.testimonial_repository.create(
            testimonial, with_relations=with_relations, commit=commit
        )

    async def get_by_id(
        self,
        testimonial_id: int,
        with_relations: Optional[TestimonialWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Testimonial]:
        return await self.testimonial_repository.get_by_id(
            testimonial_id, with_relations=with_relations, flush=flush
        )

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[TestimonialWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Testimonial]:
        return await self.testimonial_repository.get_by_public_id(
            public_id, with_relations=with_relations, flush=flush
        )

    async def list_by_user(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
        sort_order: str = "desc",
        with_relations: Optional[TestimonialWithRelations] = None,
    ) -> Page[Testimonial]:
        return await self.testimonial_repository.list_by_user(
            user_id=user_id,
            page=page,
            page_size=page_size,
            sort_order=sort_order,
            with_relations=with_relations,
        )

    async def list_public(
        self,
        is_featured: Optional[bool] = None,
        user_role: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        sort_order: str = "desc",
        with_relations: Optional[TestimonialWithRelations] = None,
    ) -> Page[Testimonial]:
        return await self.testimonial_repository.list_public(
            is_featured=is_featured,
            user_role=user_role,
            page=page,
            page_size=page_size,
            sort_order=sort_order,
            with_relations=with_relations,
        )

    async def list_all(
        self,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
        user_role: Optional[str] = None,
        is_featured: Optional[bool] = None,
        search: Optional[str] = None,
        sort_order: str = "desc",
        with_relations: Optional[TestimonialWithRelations] = None,
    ) -> Page[Testimonial]:
        return await self.testimonial_repository.list_all(
            page=page,
            page_size=page_size,
            status=status,
            user_role=user_role,
            is_featured=is_featured,
            search=search,
            sort_order=sort_order,
            with_relations=with_relations,
        )

    async def update(
        self,
        testimonial: Testimonial,
        with_relations: Optional[TestimonialWithRelations] = None,
        commit: bool = True,
    ) -> Testimonial:
        return await self.testimonial_repository.update(
            testimonial, with_relations=with_relations, commit=commit
        )

    async def delete(self, testimonial: Testimonial, commit: bool = True) -> None:
        await self.testimonial_repository.delete(testimonial, commit=commit)

