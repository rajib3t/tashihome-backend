from typing import Any, Dict, List, Optional, Sequence

from app.models.review_model import Review
from app.repositories.base_repository import Page
from app.repositories.review_repository import ReviewRepository, ReviewWithRelations


class ReviewService:
    def __init__(self, review_repository: ReviewRepository):
        self.review_repository = review_repository

    async def create(
        self,
        review: Review,
        with_relations: Optional[ReviewWithRelations] = None,
        commit: bool = True,
    ) -> Review:
        return await self.review_repository.create(
            review, with_relations=with_relations, commit=commit
        )

    async def get_by_id(
        self,
        review_id: int,
        with_relations: Optional[ReviewWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Review]:
        return await self.review_repository.get_by_id(
            review_id, with_relations=with_relations, flush=flush
        )

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[ReviewWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Review]:
        return await self.review_repository.get_by_public_id(
            public_id, with_relations=with_relations, flush=flush
        )

    async def get_by_booking_id(
        self,
        booking_id: int,
        with_relations: Optional[ReviewWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Review]:
        return await self.review_repository.get_by_booking_id(
            booking_id, with_relations=with_relations, flush=flush
        )

    async def list_by_guest(
        self,
        guest_id: int,
        page: int = 1,
        page_size: int = 10,
        sort_order: str = "desc",
        with_relations: Optional[ReviewWithRelations] = None,
    ) -> Page[Review]:
        return await self.review_repository.list_by_guest(
            guest_id=guest_id,
            page=page,
            page_size=page_size,
            sort_order=sort_order,
            with_relations=with_relations,
        )

    async def list_by_property(
        self,
        property_id: int,
        status: Optional[str] = "published",
        page: int = 1,
        page_size: int = 10,
        sort_order: str = "desc",
        with_relations: Optional[ReviewWithRelations] = None,
    ) -> Page[Review]:
        return await self.review_repository.list_by_property(
            property_id=property_id,
            status=status,
            page=page,
            page_size=page_size,
            sort_order=sort_order,
            with_relations=with_relations,
        )

    async def list_by_vendor_properties(
        self,
        property_ids: Sequence[int],
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        sort_order: str = "desc",
        with_relations: Optional[ReviewWithRelations] = None,
    ) -> Page[Review]:
        return await self.review_repository.list_by_vendor_properties(
            property_ids=property_ids,
            status=status,
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
        property_id: Optional[int] = None,
        guest_id: Optional[int] = None,
        search: Optional[str] = None,
        sort_order: str = "desc",
        with_relations: Optional[ReviewWithRelations] = None,
    ) -> Page[Review]:
        return await self.review_repository.list_all(
            page=page,
            page_size=page_size,
            status=status,
            property_id=property_id,
            guest_id=guest_id,
            search=search,
            sort_order=sort_order,
            with_relations=with_relations,
        )

    async def update(
        self,
        review: Review,
        with_relations: Optional[ReviewWithRelations] = None,
        commit: bool = True,
    ) -> Review:
        return await self.review_repository.update(
            review, with_relations=with_relations, commit=commit
        )

    async def delete(self, review: Review, commit: bool = True) -> None:
        await self.review_repository.delete(review, commit=commit)

    async def get_property_rating_summary(self, property_id: int) -> Dict[str, Any]:
        return await self.review_repository.get_property_rating_summary(property_id)

    async def get_properties_rating_summary(self, property_ids: Sequence[int]) -> Dict[int, Dict[str, Any]]:
        return await self.review_repository.get_properties_rating_summary(property_ids)


