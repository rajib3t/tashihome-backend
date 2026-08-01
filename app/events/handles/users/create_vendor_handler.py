import logging
from app.deps.service import get_email_service
from app.deps.service import get_email_template_service
from app.models.token_model import TokenType
from app.services.email_template_service import EmailTemplateService
from app.models.user_model import User
from app.core.security import TokenManager
from app.core.config import settings
from app.core.database import db as database
from app.repositories.token_repository import TokenRepository
from app.services.email_service import EmailService
from app.models.token_model import Token
from datetime import timedelta
from datetime import timezone
from datetime import datetime
from datetime import date

logger = logging.getLogger(__name__)
class CreateVendorHandler:
    @staticmethod
    async def handle(payload: User) -> None:
        user_id = payload.user_id
        email = payload.email
        public_id = str(payload.public_id)

        active_token = await TokenManager.account_activation_token(public_id)


        if settings.FRONTEND_URL:
            active_link = settings.FRONTEND_URL.rstrip("/") + f"/activate-account/{active_token}"
        else:
            active_link = f"Use this verification token to activate your account: {active_token}"


        async with database.async_session() as session:
            token_service = TokenRepository(session)
            
            tokens = await token_service.get_tokens(
                where_clause=(Token.user_id == user_id) &
                             (Token.type == TokenType.ACCOUNT_ACTIVATION)
            )
            if tokens:
                for token in tokens:
                    await token_service.delete_token(token)
            token_data = Token(
                user_id = user_id,
                token = active_token,
                expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFY_TOKEN_EXPIRE_HOURS),
                type = TokenType.ACCOUNT_ACTIVATION
            )
            await token_service.create(token_data)

            username = payload.get("full_name") or "User"
            current_year = date.today().year
            values = {
                "full_name": username,
                "activation_url": active_link,
                "expires_in": f"{settings.ACCOUNT_ACTIVATION_TOKEN_EXPIRE_HOURS} hours",
                "app_name": settings.APP_NAME,
                "year": current_year,
            }
            email_template_service = await get_email_template_service()
            html_content = await email_template_service.render_template(
                "email_verification",
                values,
                strict=True,
            )

            email_service = await get_email_service()
            try:
                await email_service.send_email(
                        to_email=email,
                        subject="Verify your email address",
                        text=(
                        f"Hi {username},\n\n"
                        "Please verify your email by clicking the link below:\n\n"
                        f"{active_link}\n\n"
                        "If you did not request this, please ignore this email."
                    ),
                    html=html_content,
                )
                logger.info("Sent registration email to %s", email)
            except Exception as exc:
                logger.error(
                    "Failed to send registration emails for %s: %s",
                    email,
                    exc,
                    exc_info=True,
                )