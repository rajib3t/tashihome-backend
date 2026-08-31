from fastapi import APIRouter, Depends

from app.api.base_controller import BaseController
from app.application.dto.host_requests.host_request import BecomeHostDTO
from app.application.use_case.user.become_host_use_case import BecomeHostUseCase
from app.deps.user import get_become_host_use_case
from app.schemas.vendor_schema import VendorResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class UserBecomeHostController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/become-host",
            tags=["User - Become Host"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            (
                "post",
                "/",
                self._become_host,
                {
                    "response_model": VendorResponseSchema,
                    "status_code": 200,
                },
            ),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _become_host(
        self,
        data: BecomeHostDTO,
        use_case: BecomeHostUseCase = Depends(get_become_host_use_case),
    ):
        result = await use_case.execute(data)
        return self.build_response(
            message="Congratulations! Your account has been upgraded to a Host.",
            data=result,
        )


controller = UserBecomeHostController()
router = controller.router

