from fastapi.params import Depends
from app.application.use_case.admin.tax.create_tax_use_case import CreateTaxUseCase
from app.application.use_case.admin.tax.delete_tax_use_case import DeleteTaxUseCase
from app.application.use_case.admin.tax.get_tax_use_case import GetTaxUseCase, ListTaxesUseCase
from app.application.use_case.admin.tax.update_tax_use_case import UpdateTaxStatusUseCase, UpdateTaxUseCase
from app.application.use_case.public.tax.get_public_taxes_use_case import GetDefaultTaxUseCase, GetPublicTaxesUseCase
from app.deps.auth import CurrentUser, require_admin, require_admin_or_staff
from app.deps.service import get_tax_service
from app.services.tax_service import TaxService


async def get_create_tax_use_case(
    tax_service: TaxService = Depends(get_tax_service),
    current_user: CurrentUser = Depends(require_admin),
) -> CreateTaxUseCase:
    return CreateTaxUseCase(tax_service=tax_service, current_user=current_user)


async def get_get_tax_use_case(
    tax_service: TaxService = Depends(get_tax_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
) -> GetTaxUseCase:
    return GetTaxUseCase(tax_service=tax_service)


async def get_list_taxes_use_case(
    tax_service: TaxService = Depends(get_tax_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
) -> ListTaxesUseCase:
    return ListTaxesUseCase(tax_service=tax_service)


async def get_update_tax_use_case(
    tax_service: TaxService = Depends(get_tax_service),
    current_user: CurrentUser = Depends(require_admin),
) -> UpdateTaxUseCase:
    return UpdateTaxUseCase(tax_service=tax_service, current_user=current_user)


async def get_update_tax_status_use_case(
    tax_service: TaxService = Depends(get_tax_service),
    current_user: CurrentUser = Depends(require_admin),
) -> UpdateTaxStatusUseCase:
    return UpdateTaxStatusUseCase(tax_service=tax_service, current_user=current_user)


async def get_delete_tax_use_case(
    tax_service: TaxService = Depends(get_tax_service),
    current_user: CurrentUser = Depends(require_admin),
) -> DeleteTaxUseCase:
    return DeleteTaxUseCase(tax_service=tax_service, current_user=current_user)


async def get_public_taxes_use_case(
    tax_service: TaxService = Depends(get_tax_service),
) -> GetPublicTaxesUseCase:
    return GetPublicTaxesUseCase(tax_service=tax_service)


async def get_default_tax_use_case(
    tax_service: TaxService = Depends(get_tax_service),
) -> GetDefaultTaxUseCase:
    return GetDefaultTaxUseCase(tax_service=tax_service)

