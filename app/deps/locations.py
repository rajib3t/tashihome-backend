from app.application.use_case.locations.city.create_city_use_case import CreateCityUseCase
from app.application.use_case.locations.city.get_cities_use_case import GetCitiesUseCase
from app.application.use_case.locations.city.update_city_use_case import UpdateCityUseCase, UpdateStatusCityUseCase
from app.deps.service import get_storage_service
from app.services.storage_service import StorageService
from app.deps.service import get_city_service
from app.services.city_service import CityService
from fastapi import Depends

from app.application.use_case.locations.country.create_country_use_case import CreateCountryUseCase
from app.application.use_case.locations.country.get_countries_use_case import GetCountriesUseCase
from app.application.use_case.locations.country.update_country_use_case import UpdateCountryUseCase, UpdateStatusCountryUseCase
from app.deps.auth import CurrentUser, get_current_user, require_admin
from app.deps.service import get_country_service
from app.services.country_service import CountryService

# Country Use Cases
async def get_countries_use_case(
    country_service: CountryService = Depends(get_country_service),
    current_user: CurrentUser = Depends(require_admin)
) -> GetCountriesUseCase:
    return GetCountriesUseCase(
        country_service=country_service,
        current_user=current_user
    )

async def get_create_country_use_case(
    country_service: CountryService = Depends(get_country_service),
    current_user: CurrentUser = Depends(require_admin)
) -> CreateCountryUseCase:
    return CreateCountryUseCase(
        country_service=country_service,
        current_user=current_user
    )


async def get_update_country_use_case(
    country_service: CountryService = Depends(get_country_service),
    current_user: CurrentUser = Depends(require_admin)
) -> UpdateCountryUseCase:
    return UpdateCountryUseCase(
        country_service=country_service,
        current_user=current_user,
    )


async def get_update_status_country_use_case(
    country_service: CountryService = Depends(get_country_service),
    current_user: CurrentUser = Depends(require_admin)
) -> UpdateStatusCountryUseCase:
    return UpdateStatusCountryUseCase(
        country_service=country_service,
        current_user=current_user,
    )



async def get_create_city_use(
    city_service: CityService = Depends(get_city_service),
    storage_service: StorageService = Depends(get_storage_service),
    country_service: CountryService = Depends(get_country_service),
    current_user: CurrentUser = Depends(require_admin)
) -> CreateCityUseCase:
    return CreateCityUseCase(
        service=city_service,
        storage_service=storage_service,
        country_service=country_service,
        current_user=current_user,
    )

async def get_city_list_use_case(
    city_service: CityService = Depends(get_city_service),
    country_service: CountryService = Depends(get_country_service),
    storage_service: StorageService = Depends(get_storage_service),
     current_user: CurrentUser = Depends(require_admin)
) -> GetCitiesUseCase:
    return GetCitiesUseCase(
        service=city_service,
        country_service=country_service,
        storage_service=storage_service,
        current_user=current_user
    )

async def get_update_city_use_case(
    city_service: CityService = Depends(get_city_service),
    country_service: CountryService = Depends(get_country_service),
    storage_service: StorageService = Depends(get_storage_service),
    current_user: CurrentUser = Depends(require_admin),
) -> UpdateCityUseCase:
    return UpdateCityUseCase(
        service=city_service,
        country_service=country_service,
        storage_service=storage_service,
        current_user=current_user,
    )
    

async def get_update_city_status_use_case(
    city_service: CityService = Depends(get_city_service),
    current_user: CurrentUser = Depends(require_admin),
) -> UpdateStatusCityUseCase:
    return UpdateStatusCityUseCase(
        service=city_service,
        current_user=current_user,
    )
    