from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.tax_model import Tax, TaxStatus
from app.services.tax_service import TaxService


class DeleteTaxUseCase(BaseUseCase):
    def __init__(
        self,
        tax_service: TaxService,
        current_user: CurrentUser,
    ):
        self.tax_service = tax_service
        self.current_user = current_user

    async def execute(self, identifier: str, hard_delete: bool = False) -> None:
        tax = await self.tax_service.get_by_identifier(identifier)
        if not tax:
            raise AppException(
                status_code=404,
                message=f"Tax with identifier '{identifier}' not found.",
                error_code="TAX_NOT_FOUND",
            )

        if hard_delete:
            await self.tax_service.delete_tax(tax, commit=True)
        else:
            tax.status = TaxStatus.INACTIVE
            tax.updated_by = self.current_user.id
            await self.tax_service.update_tax(tax, commit=True)

