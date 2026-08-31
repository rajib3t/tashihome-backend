from fastapi import APIRouter, Depends

from app.api.base_controller import BaseController
from app.application.dto.host_requests.host_request import CreateHostRequestDTO
from app.application.use_case.public.host_request.submit_host_request_use_case import (
    SubmitHostRequestUseCase,
)
from app.deps.host_request import get_submit_host_request_use_case
from app.schemas.host_request_schema import HostRequestSingleResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class PublicHostRequestController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/become-host",
            tags=["Public - Become Host"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            (
                "post",
                "/",
                self._submit_host_request,
                {
                    "response_model": HostRequestSingleResponseSchema,
                    "status_code": 201,
                },
            ),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _submit_host_request(
        self,
        data: CreateHostRequestDTO,
        use_case: SubmitHostRequestUseCase = Depends(get_submit_host_request_use_case),
    ):
        result = await use_case.execute(data)
        return self.build_response(
            message="Your request to become a host has been submitted successfully. Our team will review your application and contact you.",
            data=result,
        )


controller = PublicHostRequestController()
router = controller.router

