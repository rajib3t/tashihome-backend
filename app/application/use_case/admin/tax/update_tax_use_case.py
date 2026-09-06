from app.application.dto.tax import TaxStatusUpdateDTO, TaxUpdateDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.tax_model import Tax, TaxStatus
from app.services.tax_service import TaxService


class UpdateTaxUseCase(BaseUseCase):
    def __init__(
        self,
        tax_service: TaxService,
        current_user: CurrentUser,
    ):
        self.tax_service = tax_service
        self.current_user = current_user

    async def execute(self, identifier: str, dto: TaxUpdateDTO) -> Tax:
        tax = await self.tax_service.get_by_identifier(identifier)
        if not tax:
            raise AppException(
                status_code=404,
                message=f"Tax with identifier '{identifier}' not found.",
                error_code="TAX_NOT_FOUND",
            )

        if dto.code is not None:
            norm_code = dto.code.strip().upper()
            if norm_code != tax.code:
                existing = await self.tax_service.get_by_code(norm_code)
                if existing and existing.id != tax.id:
                    raise AppException(
                        status_code=409,
                        message=f"Tax with code '{norm_code}' already exists.",
                        error_code="TAX_CODE_ALREADY_EXISTS",
                        field="code",
                    )
                tax.code = norm_code

        if dto.name is not None:
            tax.name = dto.name.strip()
        if dto.rate is not None:
            tax.rate = dto.rate
        if dto.tax_type is not None:
            tax.tax_type = dto.tax_type
        if dto.is_inclusive is not None:
            tax.is_inclusive = dto.is_inclusive
        if dto.is_default is not None:
            tax.is_default = dto.is_default
        if dto.gst_number is not None:
            tax.gst_number = dto.gst_number.strip() if dto.gst_number else None
        if dto.legal_name is not None:
            tax.legal_name = dto.legal_name.strip() if dto.legal_name else None
        if dto.address is not None:
            tax.address = dto.address.strip() if dto.address else None
        if dto.hsn_sac_code is not None:
            tax.hsn_sac_code = dto.hsn_sac_code.strip() if dto.hsn_sac_code else None
        if dto.cgst_rate is not None:
            tax.cgst_rate = dto.cgst_rate
        if dto.sgst_rate is not None:
            tax.sgst_rate = dto.sgst_rate
        if dto.igst_rate is not None:
            tax.igst_rate = dto.igst_rate
        if dto.description is not None:
            tax.description = dto.description.strip() if dto.description else None
        if dto.status is not None:
            tax.status = dto.status

        tax.updated_by = self.current_user.id
        return await self.tax_service.update_tax(tax, commit=True)


class UpdateTaxStatusUseCase(BaseUseCase):
    def __init__(
        self,
        tax_service: TaxService,
        current_user: CurrentUser,
    ):
        self.tax_service = tax_service
        self.current_user = current_user

    async def execute(self, identifier: str, status: TaxStatus) -> Tax:
        tax = await self.tax_service.get_by_identifier(identifier)
        if not tax:
            raise AppException(
                status_code=404,
                message=f"Tax with identifier '{identifier}' not found.",
                error_code="TAX_NOT_FOUND",
            )

        tax.status = status
        tax.updated_by = self.current_user.id
        return await self.tax_service.update_tax(tax, commit=True)

