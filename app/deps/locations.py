from fastapi import Depends

from app.application.use_case.locations.country.get_countries_use_case import GetCountriesUseCase
from app.deps.auth import CurrentUser, get_current_user
from app.deps.service import get_country_service
from app.services.country_service import CountryService


async def get_countries_use_case(
    country_service: CountryService = Depends(get_country_service),
    current_user: CurrentUser = Depends(get_current_user)
) -> GetCountriesUseCase:
    return GetCountriesUseCase(
        country_service=country_service,
        current_user=current_user
    )