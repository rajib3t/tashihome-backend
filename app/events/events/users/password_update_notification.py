from app.core.events import DomainEvent


class ResetPasswordEvent(DomainEvent):
    def __init__(self, payload: dict[str, int | str]):
        super().__init__(name="user.reset_password", payload=payload)