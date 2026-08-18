from app.core.events import DomainEvent


class ForgotPasswordEvent(DomainEvent):
    def __init__(self, payload: dict[str, int | str]):
        super().__init__(name="user.forgot_password", payload=payload)