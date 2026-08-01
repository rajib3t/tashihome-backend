
from app.deps.event_bus import get_event_bus
from app.core.events import EventBus
from fastapi.params import Depends

from app.application.use_case.admin.vendors.create_vendor_use_case import CreateVendorUseCase
from app.core.csrf import verify_csrf
from app.deps.auth import CurrentUser, require_admin
from app.deps.service import get_user_service
from app.services.user_service import UserService


async def get_create_vendor_use_case(
    user_service: UserService = Depends(get_user_service),
    event_bus: EventBus = Depends(get_event_bus),
    verify_csrf=Depends(verify_csrf),
    current_user: CurrentUser = Depends(require_admin),
) -> CreateVendorUseCase:
    return CreateVendorUseCase(
        user_service=user_service,
        event_bus=event_bus,
        verify_csrf=verify_csrf,
        current_user=current_user,
    )