from app.deps.locations import get_create_city_use
from fastapi import Depends
from app.application.use_case.locations.city.create_city_use_case import CreateCityUseCase
from fastapi import APIRouter, File, Form, UploadFile
from typing import Optional

from app.api.base_controller import BaseController
from app.application.dto.locations.city import CityDTO
from app.schemas.city_schema import CityListResponseSchema, CityResponseSchema


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
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)


    async def _get_cities(self):
        # Placeholder for city retrieval logic
        return self.build_response(
            message="Cities retrieved successfully.",
            data=[]  # Replace with actual data
        )

    async def _create_city(
        self,
        name: str = Form(...),
        country_id: str = Form(...),
        image_url: Optional[UploadFile] = File(None),
        use_case : CreateCityUseCase = Depends(get_create_city_use)
    ):

        payload = CityDTO(
            name=name,
            country_id=country_id,
            image_url=image_url
        )
        city = await use_case.execute(payload)
        return self.build_response(
            message="City created successfully.",
            data=city
        )

controller = CityController()
router = controller.router