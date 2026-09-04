from typing import Any, Dict, List, Optional, Sequence, TypedDict

from sqlalchemy import func, or_, select

from app.models.property_model import Property
from app.models.review_model import Review, ReviewStatus
from app.models.user_model import User
from app.repositories.base_repository import BaseRepository, Page


class ReviewWithRelations(TypedDict, total=False):
    booking: bool
    guest: bool
    property: bool


def _parse_review_status(status: Optional[str | ReviewStatus]) -> Optional[ReviewStatus]:
    if not status:
        return None
    if isinstance(status, ReviewStatus):
        return status
    try:
        return ReviewStatus(status.lower())
    except ValueError:
        try:
            return ReviewStatus[status.upper()]
        except KeyError:
            return None


class ReviewRepository(BaseRepository[Review]):
    _relation_map = {
        "booking": Review.booking,
        "guest": Review.guest,
        "property": Review.property,
    }

    async def create(
        self,
        review: Review,
        with_relations: Optional[ReviewWithRelations] = None,
        commit: bool = True,
    ) -> Review:
        self.db.add(review)
        if commit:
            await self.db.commit()
            await self.db.refresh(review)
        if with_relations:
            query = self._apply_relations(
                select(Review).where(Review.id == review.id),
                with_relations,
                self._relation_map,
            )
            reloaded = await self._fetch_one(query)
            if reloaded:
                return reloaded
        return review

    async def get_by_id(
        self,
        review_id: int,
        with_relations: Optional[ReviewWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Review]:
        query = select(Review).where(Review.id == review_id)
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[ReviewWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Review]:
        query = select(Review).where(Review.public_id == public_id)
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._fetch_one(query, flush=flush)

    async def get_by_booking_id(
        self,
        booking_id: int,
        with_relations: Optional[ReviewWithRelations] = None,
        flush: bool = False,
    ) -> Optional[Review]:
        query = select(Review).where(Review.booking_id == booking_id)
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._fetch_one(query, flush=flush)

    async def list_by_guest(
        self,
        guest_id: int,
        page: int = 1,
        page_size: int = 10,
        sort_order: str = "desc",
        with_relations: Optional[ReviewWithRelations] = None,
        flush: bool = False,
    ) -> Page[Review]:
        query = select(Review).where(Review.guest_id == guest_id)
        if sort_order.lower() == "asc":
            query = query.order_by(Review.created_at.asc())
        else:
            query = query.order_by(Review.created_at.desc())

        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)

    async def list_by_property(
        self,
        property_id: int,
        status: Optional[str | ReviewStatus] = "published",
        page: int = 1,
        page_size: int = 10,
        sort_order: str = "desc",
        with_relations: Optional[ReviewWithRelations] = None,
        flush: bool = False,
    ) -> Page[Review]:
        query = select(Review).where(Review.property_id == property_id)
        status_enum = _parse_review_status(status)
        if status_enum is not None:
            query = query.where(Review.status == status_enum)

        if sort_order.lower() == "asc":
            query = query.order_by(Review.created_at.asc())
        else:
            query = query.order_by(Review.created_at.desc())

        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)

    async def list_by_vendor_properties(
        self,
        property_ids: Sequence[int],
        status: Optional[str | ReviewStatus] = None,
        page: int = 1,
        page_size: int = 10,
        sort_order: str = "desc",
        with_relations: Optional[ReviewWithRelations] = None,
        flush: bool = False,
    ) -> Page[Review]:
        if not property_ids:
            return Page(items=[], total=0, page=page, page_size=page_size)

        query = select(Review).where(Review.property_id.in_(property_ids))
        status_enum = _parse_review_status(status)
        if status_enum is not None:
            query = query.where(Review.status == status_enum)

        if sort_order.lower() == "asc":
            query = query.order_by(Review.created_at.asc())
        else:
            query = query.order_by(Review.created_at.desc())

        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)

    async def list_all(
        self,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str | ReviewStatus] = None,
        property_id: Optional[int] = None,
        guest_id: Optional[int] = None,
        search: Optional[str] = None,
        sort_order: str = "desc",
        with_relations: Optional[ReviewWithRelations] = None,
        flush: bool = False,
    ) -> Page[Review]:
        query = select(Review)

        status_enum = _parse_review_status(status)
        if status_enum is not None:
            query = query.where(Review.status == status_enum)

        if property_id:
            query = query.where(Review.property_id == property_id)

        if guest_id:
            query = query.where(Review.guest_id == guest_id)

        if search:
            term = f"%{search.strip()}%"
            query = (
                query.outerjoin(Review.guest)
                .outerjoin(Review.property)
                .where(
                    or_(
                        Review.comment.ilike(term),
                        User.full_name.ilike(term),
                        User.email.ilike(term),
                        Property.name.ilike(term),
                    )
                )
            )

        if sort_order.lower() == "asc":
            query = query.order_by(Review.created_at.asc())
        else:
            query = query.order_by(Review.created_at.desc())

        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)

    async def update(
        self,
        review: Review,
        with_relations: Optional[ReviewWithRelations] = None,
        commit: bool = True,
    ) -> Review:
        self.db.add(review)
        if commit:
            await self.db.commit()
            await self.db.refresh(review)
        if with_relations:
            query = self._apply_relations(
                select(Review).where(Review.id == review.id),
                with_relations,
                self._relation_map,
            )
            reloaded = await self._fetch_one(query)
            if reloaded:
                return reloaded
        return review

    async def delete(self, review: Review, commit: bool = True) -> None:
        await self.db.delete(review)
        if commit:
            await self.db.commit()

    async def get_property_rating_summary(self, property_id: int) -> Dict[str, Any]:
        """Calculates published review count, average rating, and rating distribution."""
        base_query = select(Review.rating, func.count(Review.id)).where(
            Review.property_id == property_id,
            Review.status == ReviewStatus.PUBLISHED,
        ).group_by(Review.rating)

        result = await self.db.execute(base_query)
        rows = result.all()

        distribution = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        total_reviews = 0
        total_score = 0

        for rating, count in rows:
            if rating is not None:
                rating_str = str(rating)
                if rating_str in distribution:
                    distribution[rating_str] = count
                total_reviews += count
                total_score += rating * count

        average_rating = round(total_score / total_reviews, 2) if total_reviews > 0 else 0.0

        return {
            "average_rating": average_rating,
            "total_reviews": total_reviews,
            "rating_distribution": distribution,
        }

    async def get_properties_rating_summary(self, property_ids: Sequence[int]) -> Dict[int, Dict[str, Any]]:
        """Calculates published review count, average rating, and rating distribution for multiple properties."""
        if not property_ids:
            return {}

        query = select(
            Review.property_id,
            Review.rating,
            func.count(Review.id),
        ).where(
            Review.property_id.in_(property_ids),
            Review.status == ReviewStatus.PUBLISHED,
        ).group_by(Review.property_id, Review.rating)

        result = await self.db.execute(query)
        rows = result.all()

        summary_by_property = {
            pid: {
                "average_rating": 0.0,
                "total_reviews": 0,
                "rating_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
            }
            for pid in property_ids
        }

        property_scores = {pid: 0 for pid in property_ids}

        for prop_id, rating, count in rows:
            if prop_id in summary_by_property and rating is not None:
                rating_str = str(rating)
                if rating_str in summary_by_property[prop_id]["rating_distribution"]:
                    summary_by_property[prop_id]["rating_distribution"][rating_str] = count
                summary_by_property[prop_id]["total_reviews"] += count
                property_scores[prop_id] += rating * count

        for pid, data in summary_by_property.items():
            tot = data["total_reviews"]
            if tot > 0:
                data["average_rating"] = round(property_scores[pid] / tot, 2)

        return summary_by_property


