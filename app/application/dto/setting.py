from datetime import datetime
from typing import Optional, Union
from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict, field_validator


class SettingUpdateDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    # General / Branding
    app_name: Optional[str] = None
    app_logo: Optional[Union[str, UploadFile]] = None
    white_logo: Optional[Union[str, UploadFile]] = None
    app_favicon: Optional[Union[str, UploadFile]] = None
    app_timezone: Optional[str] = None
    app_date_format: Optional[str] = None
    app_time_format: Optional[str] = None
    default_currency: Optional[str] = None
    currency_symbol: Optional[str] = None

    # Contact & Support
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_address: Optional[str] = None

    # Homestay & Booking / Financial Settings
    default_commission_percentage: Optional[Union[float, str]] = None
    service_fee_percentage: Optional[Union[float, str]] = None
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    min_booking_days: Optional[Union[int, str]] = None
    max_booking_days: Optional[Union[int, str]] = None
    cancellation_grace_period_hours: Optional[Union[int, str]] = None

    # Social Links
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    youtube_url: Optional[str] = None

    # SEO & Policies
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    terms_and_conditions_url: Optional[str] = None
    privacy_policy_url: Optional[str] = None
    refund_policy_url: Optional[str] = None

    # Coming Soon Settings
    is_enabled_coming_soon: Optional[Union[bool, str]] = None
    launch_date: Optional[datetime] = None
    coming_soon_message: Optional[str] = None
    coming_background_image: Optional[Union[str, UploadFile]] = None
    coming_soon_video: Optional[Union[str, UploadFile]] = None

    @field_validator(
        'is_enabled_coming_soon',
        mode='before'
    )
    @classmethod
    def convert_bool_to_str(cls, v):
        if isinstance(v, bool):
            return str(v).lower()
        return v
