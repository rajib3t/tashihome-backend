from fastapi import APIRouter, Depends

from app.api.base_controller import BaseController
from app.application.dto.bookings.refund import AdminRefundQueryDTO, AdminRefundStatusUpdateDTO
from app.application.use_case.admin.bookings.list_refund_requests_use_case import AdminListRefundRequestsUseCase
from app.application.use_case.admin.bookings.get_refund_request_use_case import AdminGetRefundRequestUseCase
from app.application.use_case.admin.bookings.update_refund_request_use_case import (
    AdminUpdateRefundStatusUseCase,
    AdminProcessRefundUseCase,
)
from app.deps.booking import (
    get_admin_list_refund_requests_use_case,
    get_admin_get_refund_request_use_case,
    get_admin_update_refund_status_use_case,
    get_admin_process_refund_use_case,
)
from app.schemas.refund_request_schema import (
    RefundRequestListResponseSchema,
    RefundRequestResponseSchema,
    ProcessRefundResponseSchema,
)
from app.utils.exception_decorate import handle_api_exceptions


class AdminRefundController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/refunds",
            tags=["Admin - Refunds"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            (
                "get",
                "/",
                self._list_refund_requests,
                {"response_model": RefundRequestListResponseSchema},
            ),
            (
                "get",
                "/{refund_request_id}",
                self._get_refund_request,
                {"response_model": RefundRequestResponseSchema},
            ),
            (
                "patch",
                "/{refund_request_id}/status",
                self._update_refund_status,
                {"response_model": RefundRequestResponseSchema},
            ),
            (
                "post",
                "/{refund_request_id}/process",
                self._process_refund,
                {"response_model": ProcessRefundResponseSchema},
            ),
        ]
        for method, path, handler, kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **kwargs)

    @handle_api_exceptions
    async def _list_refund_requests(
        self,
        params: AdminRefundQueryDTO = Depends(),
        use_case: AdminListRefundRequestsUseCase = Depends(get_admin_list_refund_requests_use_case),
    ):
        page = await use_case.execute(params)
        return self.build_response(
            message="Refund requests retrieved successfully.",
            data=page.items,
            meta=self.pagination_meta(page),
        )

    @handle_api_exceptions
    async def _get_refund_request(
        self,
        refund_request_id: str,
        use_case: AdminGetRefundRequestUseCase = Depends(get_admin_get_refund_request_use_case),
    ):
        refund_request = await use_case.execute(refund_request_id)
        return self.build_response(
            message="Refund request retrieved successfully.",
            data=refund_request,
        )

    @handle_api_exceptions
    async def _update_refund_status(
        self,
        refund_request_id: str,
        data: AdminRefundStatusUpdateDTO,
        use_case: AdminUpdateRefundStatusUseCase = Depends(get_admin_update_refund_status_use_case),
    ):
        refund_request = await use_case.execute(refund_request_id, data)
        return self.build_response(
            message="Refund request status updated successfully.",
            data=refund_request,
        )

    @handle_api_exceptions
    async def _process_refund(
        self,
        refund_request_id: str,
        use_case: AdminProcessRefundUseCase = Depends(get_admin_process_refund_use_case),
    ):
        result = await use_case.execute(refund_request_id)
        return self.build_response(
            message="Refund processed successfully.",
            data=result,
        )


controller = AdminRefundController()
router = controller.router

