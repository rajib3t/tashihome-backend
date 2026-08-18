from app.events.handles.users.forgot_password_handler import ForgotPasswordHandler
from app.events.handles.users.create_user_handler import CreateUserHandler
from app.events.handles.users.create_vendor_handler import CreateVendorHandler
import asyncio
import json
import logging
from typing import Awaitable, Callable

from app.core.events import RedisEventSubscriber

logger = logging.getLogger(__name__)

EventHandler = Callable[[dict], Awaitable[None]]

HANDLERS: dict[str, EventHandler] = {
   "user.vendor.created": CreateVendorHandler.handle,
   "user.created": CreateUserHandler.handle,
   "user.forgot_password": ForgotPasswordHandler.handle,
}


async def start_event_subscriber() -> None:
    subscriber = RedisEventSubscriber()
    await subscriber.listen(HANDLERS)