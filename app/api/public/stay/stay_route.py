from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.api.base_controller import BaseController
from app.application.dto.bookings.booking import BookingAvailabilityDTO
from app.application.dto.stays.public.stay import PublicSearchStaysQueryDTO
from app.application.use_case.public.property.get_property_use_case import PublicGetPropertyUseCase
from app.application.use_case.public.stay.search_stays_use_case import PublicSearchStaysUseCase
from app.application.use_case.user.booking.check_availability_use_case import CheckAvailabilityUseCase
from app.deps.booking import get_check_availability_use_case
from app.deps.public.stay import public_get_stay_use_case, public_search_stays_use_case
from app.schemas.booking_schema import BookingAvailabilityResponseSchema
from app.schemas.public.stay_schema import PublicStayListResponseSchema, PublicStayResponse
from app.utils.exception_decorate import handle_api_exceptions


class PublicStayController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/stays",
            tags=["Public - Stays"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._search_stays, {"response_model": PublicStayListResponseSchema}),
            ("get", "/search", self._search_stays, {"response_model": PublicStayListResponseSchema}),
            ("post", "/check-availability", self._check_availability, {"response_model": BookingAvailabilityResponseSchema}),
            ("get", "/{slug}", self._get_stay, {"response_model": PublicStayResponse}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _search_stays(
        self,
        params: PublicSearchStaysQueryDTO = Depends(),
        use_case: PublicSearchStaysUseCase = Depends(public_search_stays_use_case),
    ):
        stays = await use_case.execute(params)
        return self.build_response(
            message="Stays retrieved successfully.",
            data=stays.items,
            meta=self.pagination_meta(stays),
        )

    @handle_api_exceptions
    async def _check_availability(
        self,
        data: BookingAvailabilityDTO,
        use_case: CheckAvailabilityUseCase = Depends(get_check_availability_use_case),
    ):
        result = await use_case.execute(data)
        return self.build_response(
            message="Availability check completed.",
            data=result,
        )

    @handle_api_exceptions
    async def _get_stay(
        self,
        slug: str,
        check_in_date: Optional[date] = Query(default=None),
        check_out_date: Optional[date] = Query(default=None),
        use_case: PublicGetPropertyUseCase = Depends(public_get_stay_use_case),
    ):
        stay_data = await use_case.execute(
            slug=slug,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
        )
        return self.build_response(
            message="Stay retrieved successfully.",
            data=stay_data,
        )


controller = PublicStayController()
router = controller.router
