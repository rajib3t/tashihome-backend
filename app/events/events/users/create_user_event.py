from app.core.events import DomainEvent
from app.models.user_model import User


class CreateUserEvent(DomainEvent):
    def __init__(self, user: User):
        payload = {
            "id": int(user.id),
            "public_id": str(user.public_id),
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "is_subscribed":user.is_subscribed
        }
        super().__init__(name="user.created", payload=payload)
