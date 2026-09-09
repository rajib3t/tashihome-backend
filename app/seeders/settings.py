import argparse
import asyncio
import os
import sys
from typing import Dict

from app.core.database import db
from app.models.setting_model import Setting
from app.repositories.setting_repository import SettingRepository

DEFAULT_SETTINGS: Dict[str, str] = {
    # General / Branding
    "app_name": "Tashi Homestay & Hospitality",
    "assistant_name": "Jitu",
    "default_currency": "INR",
    "currency_symbol": "₹",
    "app_timezone": "Asia/Kolkata",
    "app_date_format": "DD/MM/YYYY",
    "app_time_format": "12",

    # Contact & Support
    "contact_email": "support@tashihome.in",
    "contact_phone": "+91 9876543210",
    "contact_address": "MG Marg, Gangtok, Sikkim - 737101, India",
    "contact_whatsapp": "+91 9876543210",

    # Social Media
    "facebook_url": "https://www.facebook.com/tashihome",
    "instagram_url": "https://www.instagram.com/tashihome",
    "twitter_url": "https://x.com/tashihome",
    "linkedin_url": "https://www.linkedin.com/company/tashihome",
    "youtube_url": "https://www.youtube.com/@tashihome",

    # SEO & Policies
    "meta_title": "Tashi Homestay - Authentic Stays & Himalayan Hospitality",
    "meta_description": "Book verified homestays, heritage mountain cottages, and local hospitality experiences across Sikkim and Northeast India.",
    "meta_keywords": "homestays, sikkim homestay, gangtok stays, himalayan retreats, tashi homestay, budget stays",
    "terms_and_conditions_url": "https://tashihome.in/terms",
    "privacy_policy_url": "https://tashihome.in/privacy",
    "refund_policy_url": "https://tashihome.in/refund",

    # Homestay & Booking Policies
    "check_in_time": "14:00",
    "check_out_time": "11:00",
    "min_booking_days": "1",
    "max_booking_days": "30",
    "cancellation_grace_period_hours": "24",
    "default_commission_percentage": "10.0",
    "service_fee_percentage": "2.5",

    # Coming Soon Settings
    "is_enabled_coming_soon": "false",
    "coming_soon_message": "We are preparing something exceptional for your next mountain getaway! Stay tuned.",
}


async def seed_settings(overwrite: bool = False) -> dict[str, int]:
    db.connect()
    created_count = 0
    updated_count = 0

    try:
        async with db.async_session() as session:
            repository = SettingRepository(session)
            existing_settings = await repository.get_all(flush=True)
            existing_map = {s.key: s for s in existing_settings}

            for key, default_val in DEFAULT_SETTINGS.items():
                if key in existing_map:
                    if overwrite:
                        setting = existing_map[key]
                        setting.value = default_val
                        await repository.save(setting, commit=False)
                        updated_count += 1
                else:
                    new_setting = Setting(key=key, value=default_val)
                    await repository.save(new_setting, commit=False)
                    created_count += 1

            await session.commit()
    finally:
        await db.disconnect()

    return {"created": created_count, "updated": updated_count}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed default platform and public settings")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing setting values with default seed values",
    )
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    print("🌱 Seeding default platform and public settings...")
    try:
        counts = await seed_settings(overwrite=args.overwrite)
        print(f"✅ Seeding complete! Created: {counts['created']}, Updated: {counts['updated']}")
        return 0
    except Exception as exc:
        print(f"❌ Failed to seed settings: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

