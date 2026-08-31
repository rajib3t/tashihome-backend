from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.models.payout_model import Payout
from app.services.payout_service import PayoutService

_RELATIONS = {
    "vendor": True,
    "bank_account": True,
    "creator": True,
}


class GetPayoutUseCase(BaseUseCase):
    def __init__(self, payout_service: PayoutService):
        self.payout_service = payout_service

    async def execute(self, payout_id: str) -> Payout:
        payout = await self.payout_service.get_by_public_id(
            payout_id,
            with_relations=_RELATIONS,
        )
        if not payout:
            raise AppException(
                status_code=404,
                message="Payout record not found.",
                error_code="PAYOUT_NOT_FOUND",
                field="payout_id",
            )
        return payout

