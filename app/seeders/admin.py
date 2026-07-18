import argparse
import asyncio
import os
import sys

from app.core.database import db
from app.core.security import PasswordHasher
from app.models.user_model import User, UserRole, UserStatus
from app.repositories.user_repository import UserRepository 


async def build_admin_payload(email: str, password: str, phone: str, full_name: str | None = None) -> dict:
    if not email:
        raise ValueError("Super admin email is required")
    if not password:
        raise ValueError("Super admin password is required")
    if not phone:
        raise ValueError("Super admin phone is required")

    return {
        "email": email,
        "phone": phone,
        "full_name": full_name or email.split("@", 1)[0].replace(".", " ").title(),
        "password": await PasswordHasher().hash_password(password),
        "role": UserRole.ADMIN,
        "status": UserStatus.ACTIVE,
        "is_terms_accepted": True,
        "is_subscribed": True,
        "is_profile_image_url": None,
    }


async def ensure_admin(email: str, password: str, phone: str, full_name: str | None = None):
    payload = await build_admin_payload(email=email, password=password, phone=phone, full_name=full_name)

    db.connect()
    try:
        async with db.async_session() as session:
            repository = UserRepository(session)
            existing_user = await repository.get_by_email(email, with_relations=None, flush=True)

            if existing_user:
                existing_user.full_name = payload["full_name"]
                existing_user.phone = payload["phone"]
                existing_user.role = payload["role"]
                existing_user.status = payload["status"]
                existing_user.is_subscribed = payload["is_subscribed"]
                existing_user.is_terms_accepted = payload["is_terms_accepted"]
                existing_user.password = payload["password"]
                existing_user.is_profile_image_url = payload.get("is_profile_image_url", existing_user.is_profile_image_url)
                return await repository.update(existing_user)

            new_user = User(**payload)
            return await repository.create(new_user, with_relations=None, commit=True)
    finally:
        await db.disconnect()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or update a super admin user")
    parser.add_argument("--email", default=os.getenv("SUPERADMIN_EMAIL"), help="Super admin email")
    parser.add_argument("--password", default=os.getenv("SUPERADMIN_PASSWORD"), help="Super admin password")
    parser.add_argument("--phone", default=os.getenv("SUPERADMIN_PHONE"), help="Super admin phone number")
    parser.add_argument(
        "--full-name",
        default=os.getenv("SUPERADMIN_FULL_NAME"),
        help="Super admin full name",
    )
    return parser.parse_args()


async def main() -> int:
    args = parse_args()

    try:
        user = await ensure_admin(
            email=args.email,
            password=args.password,
            phone=args.phone,
            full_name=args.full_name,
        )
    except Exception as exc:  # pragma: no cover - CLI error path
        print(f"Failed to create super admin: {exc}", file=sys.stderr)
        return 1

    print(
        f"Super admin ready: email={user.email}, role={user.role.value if hasattr(user.role, 'value') else user.role}, status={user.status.value if hasattr(user.status, 'value') else user.status}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
