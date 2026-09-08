from typing import Optional
from app.application.dto.assistant.assistant import AssistantChatRequestDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.deps.auth import CurrentUser
from app.schemas.assistant_schema import AssistantChatDataSchema
from app.services.assistant_service import AssistantService


class ChatAssistantUseCase(BaseUseCase):
    def __init__(self, assistant_service: AssistantService):
        self.assistant_service = assistant_service

    async def execute(
        self,
        data: AssistantChatRequestDTO,
        current_user: Optional[CurrentUser] = None,
    ) -> AssistantChatDataSchema:
        history = [h.model_dump() for h in (data.conversation_history or [])]

        guest_details = {}
        if data.guest_name:
            guest_details["guest_name"] = data.guest_name
        if data.guest_email:
            guest_details["guest_email"] = str(data.guest_email)
        if data.guest_phone:
            guest_details["guest_phone"] = data.guest_phone
        if data.guest_password:
            guest_details["guest_password"] = data.guest_password

        current_user_id = current_user.id if current_user else None

        result = await self.assistant_service.chat(
            message=data.message,
            conversation_history=history,
            session_id=data.session_id,
            current_user_id=current_user_id,
            guest_details=guest_details,
        )

        return result

