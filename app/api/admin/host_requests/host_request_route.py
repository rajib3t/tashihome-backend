from fastapi import APIRouter, Depends

from app.api.base_controller import BaseController
from app.application.dto.host_requests.host_request import (
    AddHostRequestMessageDTO,
    ConvertHostRequestDTO,
    HostRequestQueryDTO,
    UpdateHostRequestStatusDTO,
)
from app.application.use_case.admin.host_requests.add_host_request_message_use_case import (
    AddHostRequestMessageUseCase,
)
from app.application.use_case.admin.host_requests.convert_host_request_use_case import (
    ConvertHostRequestUseCase,
)
from app.application.use_case.admin.host_requests.get_host_request_use_case import (
    GetHostRequestUseCase,
)
from app.application.use_case.admin.host_requests.list_host_requests_use_case import (
    ListHostRequestsUseCase,
)
from app.application.use_case.admin.host_requests.update_host_request_status_use_case import (
    UpdateHostRequestStatusUseCase,
)
from app.deps.host_request import (
    get_add_host_request_message_use_case,
    get_convert_host_request_use_case,
    get_get_host_request_use_case,
    get_list_host_requests_use_case,
    get_update_host_request_status_use_case,
)
from app.schemas.host_request_schema import (
    HostRequestListResponseSchema,
    HostRequestSingleResponseSchema,
)
from app.schemas.vendor_schema import VendorResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class AdminHostRequestController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/host-requests",
            tags=["Admin - Host Requests"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            (
                "get",
                "/",
                self._get_host_requests,
                {"response_model": HostRequestListResponseSchema},
            ),
            (
                "get",
                "/{request_id}",
                self._get_host_request,
                {"response_model": HostRequestSingleResponseSchema},
            ),
            (
                "patch",
                "/{request_id}/status",
                self._update_host_request_status,
                {"response_model": HostRequestSingleResponseSchema},
            ),
            (
                "post",
                "/{request_id}/messages",
                self._add_host_request_message,
                {"response_model": HostRequestSingleResponseSchema},
            ),
            (
                "post",
                "/{request_id}/convert",
                self._convert_host_request,
                {"response_model": VendorResponseSchema},
            ),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_host_requests(
        self,
        params: HostRequestQueryDTO = Depends(),
        use_case: ListHostRequestsUseCase = Depends(get_list_host_requests_use_case),
    ):
        requests_page = await use_case.execute(params)
        return self.build_response(
            message="Host requests retrieved successfully.",
            data=requests_page.items,
            meta=self.pagination_meta(requests_page),
        )

    @handle_api_exceptions
    async def _get_host_request(
        self,
        request_id: str,
        use_case: GetHostRequestUseCase = Depends(get_get_host_request_use_case),
    ):
        result = await use_case.execute(request_id)
        return self.build_response(
            message="Host request details retrieved successfully.",
            data=result,
        )

    @handle_api_exceptions
    async def _update_host_request_status(
        self,
        request_id: str,
        data: UpdateHostRequestStatusDTO,
        use_case: UpdateHostRequestStatusUseCase = Depends(get_update_host_request_status_use_case),
    ):
        result = await use_case.execute(request_id, data)
        return self.build_response(
            message=f"Host request status updated to '{result.status.value}'.",
            data=result,
        )

    @handle_api_exceptions
    async def _add_host_request_message(
        self,
        request_id: str,
        data: AddHostRequestMessageDTO,
        use_case: AddHostRequestMessageUseCase = Depends(get_add_host_request_message_use_case),
    ):
        result = await use_case.execute(request_id, data)
        return self.build_response(
            message="Message / review note added successfully.",
            data=result,
        )

    @handle_api_exceptions
    async def _convert_host_request(
        self,
        request_id: str,
        data: ConvertHostRequestDTO,
        use_case: ConvertHostRequestUseCase = Depends(get_convert_host_request_use_case),
    ):
        result = await use_case.execute(request_id, data)
        return self.build_response(
            message="Host application approved and converted to Host successfully.",
            data=result,
        )


controller = AdminHostRequestController()
router = controller.router

