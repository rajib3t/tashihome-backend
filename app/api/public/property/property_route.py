from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.api.base_controller import BaseController
from app.application.dto.bookings.booking import BookingAvailabilityDTO
from app.application.dto.properties.public.property import PublicPropertyQueryDTO
from app.application.dto.stays.public.stay import PublicSearchStaysQueryDTO
from app.application.use_case.public.property.get_properties_use_case import PublicPropertiesUseCase
from app.application.use_case.public.property.get_property_use_case import PublicGetPropertyUseCase
from app.application.use_case.public.stay.search_stays_use_case import PublicSearchStaysUseCase
from app.application.use_case.user.booking.check_availability_use_case import CheckAvailabilityUseCase
from app.deps.booking import get_check_availability_use_case
from app.deps.public.property import public_get_property_use_case, public_properties_use_case
from app.deps.public.stay import public_search_stays_use_case
from app.schemas.booking_schema import BookingAvailabilityResponseSchema
from app.schemas.public.property_schema import PublicPropertyResponse, PublicPropertyResponseListSchema
from app.utils.exception_decorate import handle_api_exceptions


class PublicPropertyController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/properties",
            tags=["Public - Properties"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._get_properties, {"response_model": PublicPropertyResponseListSchema}),
            ("get", "/search", self._search_properties, {"response_model": PublicPropertyResponseListSchema}),
            ("post", "/check-availability", self._check_availability, {"response_model": BookingAvailabilityResponseSchema}),
            ("get", "/{slug}", self._get_property, {"response_model": PublicPropertyResponse}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_properties(
        self,
        params: PublicPropertyQueryDTO = Depends(),
        use_case: PublicPropertiesUseCase = Depends(public_properties_use_case),
    ):
        properties = await use_case.execute(params)
        return self.build_response(
            message="Properties retrieved successfully.",
            data=properties.items,
            meta=self.pagination_meta(properties),
        )

    @handle_api_exceptions
    async def _search_properties(
        self,
        params: PublicSearchStaysQueryDTO = Depends(),
        use_case: PublicSearchStaysUseCase = Depends(public_search_stays_use_case),
    ):
        properties = await use_case.execute(params)
        return self.build_response(
            message="Properties retrieved successfully.",
            data=properties.items,
            meta=self.pagination_meta(properties),
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
    async def _get_property(
        self,
        slug: str,
        check_in_date: Optional[date] = Query(default=None),
        check_out_date: Optional[date] = Query(default=None),
        use_case: PublicGetPropertyUseCase = Depends(public_get_property_use_case),
    ):
        property_data = await use_case.execute(
            slug=slug,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
        )
        return self.build_response(
            message="Property retrieved successfully.",
            data=property_data,
        )


controller = PublicPropertyController()
router = controller.router