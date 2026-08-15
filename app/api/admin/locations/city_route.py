from app.application.use_case.admin.locations.city.get_cities_use_case import GetCitiesUseCase
from app.application.use_case.admin.locations.city.update_city_use_case import UpdateCityUseCase, UpdateStatusCityUseCase
from app.deps.locations import (
    get_city_list_use_case, 
    get_create_city_use, 
    get_update_city_use_case,
    get_update_city_status_use_case
)
from fastapi import Depends
from app.application.use_case.admin.locations.city.create_city_use_case import CreateCityUseCase
from fastapi import APIRouter, File, Form, UploadFile
from typing import Optional, Union

from app.api.base_controller import BaseController
from app.application.dto.locations.city import CityDTO, CityQueryDTO
from app.schemas.city_schema import CityListResponseSchema, CityResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class CityController(BaseController):
    def __init__(self):
            self.router = APIRouter(
                prefix="/cities",
                tags=["Cities"],
            )
            self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._get_cities, {"response_model": CityListResponseSchema, "response_model_by_alias": False}),
            ("post", "/", self._create_city, {"response_model": CityResponseSchema, "response_model_by_alias": False, "status_code": 201}),
            ("put", "/{city_id}", self._update_city, {"response_model": CityResponseSchema, "response_model_by_alias": False}),
            ("patch", "/{city_id}/{status}", self._update_city_status, {"response_model": CityResponseSchema, "response_model_by_alias": False}),
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_cities(
        self,
        params:CityQueryDTO = Depends(),
        use_case: GetCitiesUseCase = Depends(get_city_list_use_case)
    ):
        
        cities = await use_case.execute(params)

        return self.build_response(
            message="Cities retrieved successfully.",
            data=cities.items,
            meta=self.pagination_meta(cities)
        )
    @handle_api_exceptions
    async def _create_city(
        self,
        name: str = Form(...),
        country_id: str = Form(...),
        short_description: str = Form(...),
        tag_line: str = Form(...),
        is_featured: Optional[Union[bool, str]] = Form(False),
        image_url: Optional[UploadFile] = File(None),
        use_case : CreateCityUseCase = Depends(get_create_city_use)
    ):

        payload = CityDTO(
            name=name,
            country_id=country_id,
            short_description=short_description,
            tag_line=tag_line,
            is_featured=is_featured,
            image_url=image_url
        )
        city = await use_case.execute(payload)
        return self.build_response(
            message="City created successfully.",
            data=city
        )
    @handle_api_exceptions
    async def _update_city(
        self,
        city_id: str,
        name: str = Form(...),
        country_id : str = Form(...),
        short_description: str = Form(...),
        tag_line: str = Form(...),
        is_featured: Optional[Union[bool, str]] = Form(False),
        image_url : Optional[UploadFile] = File(None),
        use_case: UpdateCityUseCase = Depends(get_update_city_use_case),
    ):
        payload = CityDTO(
            name=name,
            country_id=country_id,
            image_url=image_url,
            tag_line=tag_line,
            short_description=short_description,
            is_featured=is_featured,
        )
        city = await use_case.execute(city_id, payload)
        return self.build_response(
            message="City updated successfully.",
            data=city,
        )
    @handle_api_exceptions
    async def _update_city_status(
        self,
        city_id: str,
        status: str,
        use_case: UpdateStatusCityUseCase = Depends(get_update_city_status_use_case),
    ):
        city = await use_case.execute(city_id, status)
        return self.build_response(
            message="City status updated successfully.",
            data=city,
        )

controller = CityController()
router = controller.router
