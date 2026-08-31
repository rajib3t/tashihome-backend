from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.application.use_case.public.host_request.submit_host_request_use_case import (
    SubmitHostRequestUseCase,
)
from app.core.events import EventBus
from app.deps.auth import CurrentUser, require_admin, require_admin_or_staff
from app.deps.database import get_db
from app.deps.event_bus import get_event_bus
from app.deps.service import (
    get_address_service,
    get_company_service,
    get_user_service,
)
from app.repositories.host_request_repository import HostRequestRepository
from app.services.address_service import AddressService
from app.services.company_service import CompanyService
from app.services.host_request_service import HostRequestService
from app.services.user_service import UserService


async def get_host_request_repository(
    db: AsyncSession = Depends(get_db),
) -> HostRequestRepository:
    return HostRequestRepository(db)


async def get_host_request_service(
    repo: HostRequestRepository = Depends(get_host_request_repository),
) -> HostRequestService:
    return HostRequestService(repo)


async def get_submit_host_request_use_case(
    host_request_service: HostRequestService = Depends(get_host_request_service),
    user_service: UserService = Depends(get_user_service),
) -> SubmitHostRequestUseCase:
    return SubmitHostRequestUseCase(
        host_request_service=host_request_service,
        user_service=user_service,
    )


async def get_list_host_requests_use_case(
    host_request_service: HostRequestService = Depends(get_host_request_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
) -> ListHostRequestsUseCase:
    return ListHostRequestsUseCase(
        host_request_service=host_request_service,
        current_user=current_user,
    )


async def get_get_host_request_use_case(
    host_request_service: HostRequestService = Depends(get_host_request_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
) -> GetHostRequestUseCase:
    return GetHostRequestUseCase(
        host_request_service=host_request_service,
        current_user=current_user,
    )


async def get_update_host_request_status_use_case(
    host_request_service: HostRequestService = Depends(get_host_request_service),
    user_service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
) -> UpdateHostRequestStatusUseCase:
    return UpdateHostRequestStatusUseCase(
        host_request_service=host_request_service,
        user_service=user_service,
        current_user=current_user,
    )


async def get_add_host_request_message_use_case(
    host_request_service: HostRequestService = Depends(get_host_request_service),
    user_service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
) -> AddHostRequestMessageUseCase:
    return AddHostRequestMessageUseCase(
        host_request_service=host_request_service,
        user_service=user_service,
        current_user=current_user,
    )


async def get_convert_host_request_use_case(
    host_request_service: HostRequestService = Depends(get_host_request_service),
    user_service: UserService = Depends(get_user_service),
    company_service: CompanyService = Depends(get_company_service),
    address_service: AddressService = Depends(get_address_service),
    event_bus: EventBus = Depends(get_event_bus),
    current_user: CurrentUser = Depends(require_admin_or_staff),
) -> ConvertHostRequestUseCase:
    return ConvertHostRequestUseCase(
        host_request_service=host_request_service,
        user_service=user_service,
        company_service=company_service,
        address_service=address_service,
        event_bus=event_bus,
        current_user=current_user,
    )

