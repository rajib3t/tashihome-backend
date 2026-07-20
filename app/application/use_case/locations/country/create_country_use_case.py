from app.application.dto.locations.country import CountryDTO
from app.deps.auth import CurrentUser
from app.models.country_model import Country
from app.services.country_service import CountryService


class CreateCountryUseCase:
    def __init__(
            self, 
            country_service: CountryService, 
            current_user: CurrentUser
        ):
        self.country_service = country_service
        self.current_user = current_user
    
    async def execute(self, country_data: CountryDTO) -> Country:
        # Create a new country instance using the provided data
        new_country = Country(
            name=country_data.name,
            code=country_data.code,
            
        )
        
        # Call the service to create the country
        created_country = await self.country_service.create_country(
            new_country, 
            with_relations=None, 
            commit=True
        )
        
        return created_country