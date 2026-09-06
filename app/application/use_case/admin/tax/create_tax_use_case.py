from app.application.dto.tax import TaxCreateDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.tax_model import Tax, TaxStatus, TaxType
from app.services.tax_service import TaxService


class CreateTaxUseCase(BaseUseCase):
    def __init__(
        self,
        tax_service: TaxService,
        current_user: CurrentUser,
    ):
        self.tax_service = tax_service
        self.current_user = current_user

    async def execute(self, dto: TaxCreateDTO) -> Tax:
        existing = await self.tax_service.get_by_code(dto.code)
        if existing:
            raise AppException(
                status_code=409,
                message=f"Tax with code '{dto.code}' already exists.",
                error_code="TAX_CODE_ALREADY_EXISTS",
                field="code",
            )

        tax_obj = Tax(
            name=dto.name.strip(),
            code=dto.code.strip().upper(),
            rate=dto.rate,
            tax_type=dto.tax_type or TaxType.PERCENTAGE,
            is_inclusive=bool(dto.is_inclusive),
            is_default=bool(dto.is_default),
            gst_number=dto.gst_number.strip() if dto.gst_number else None,
            legal_name=dto.legal_name.strip() if dto.legal_name else None,
            address=dto.address.strip() if dto.address else None,
            hsn_sac_code=dto.hsn_sac_code.strip() if dto.hsn_sac_code else None,
            cgst_rate=dto.cgst_rate,
            sgst_rate=dto.sgst_rate,
            igst_rate=dto.igst_rate,
            description=dto.description.strip() if dto.description else None,
            status=dto.status or TaxStatus.ACTIVE,
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
        )

        return await self.tax_service.create_tax(tax_obj, commit=True)

