from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.models.refund_request_model import RefundRequest
from app.services.refund_request_service import RefundRequestService

_RELATIONS = {
    "booking": True,
    "payment": True,
    "requester": True,
    "approver": True,
}


class AdminGetRefundRequestUseCase(BaseUseCase):
    def __init__(self, refund_request_service: RefundRequestService):
        self.refund_request_service = refund_request_service

    async def execute(self, refund_request_id: str) -> RefundRequest:
        refund_request = await self.refund_request_service.get_by_public_id(
            refund_request_id,
            with_relations=_RELATIONS,
        )
        if not refund_request:
            raise AppException(
                status_code=404,
                message="Refund request not found.",
                error_code="REFUND_REQUEST_NOT_FOUND",
                field="refund_request_id",
            )
        return refund_request

