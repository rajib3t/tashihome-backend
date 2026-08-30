from app.application.dto.bookings.refund import AdminRefundQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.repositories.base_repository import Page
from app.models.refund_request_model import RefundRequest
from app.services.refund_request_service import RefundRequestService

_RELATIONS = {
    "booking": True,
    "payment": True,
    "requester": True,
    "approver": True,
}


class AdminListRefundRequestsUseCase(BaseUseCase):
    def __init__(self, refund_request_service: RefundRequestService):
        self.refund_request_service = refund_request_service

    async def execute(self, params: AdminRefundQueryDTO) -> Page[RefundRequest]:
        booking_id = int(params.booking_id) if params.booking_id else None
        return await self.refund_request_service.list_all(
            page=params.page,
            page_size=params.size,
            status=params.status,
            booking_id=booking_id,
            sort_order=params.sort_order,
            with_relations=_RELATIONS,
        )

