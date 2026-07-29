from app.application.dto.locations.location import LocationDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.models.location_model import Location
from app.services.location_service import LocationService
from app.services.city_service import CityService
from app.deps.auth import CurrentUser

class CreateLocationUseCase(BaseUseCase):
    def __init__(
        self,
        service: LocationService,
        city_service : CityService,
        current_user : CurrentUser
    ):
        self.service = service
        self.city_service = city_service
        self.current_user = current_user
    
    def execute(self, location_data: LocationDTO) -> Location:

        
        return self.service.create_location(location_data)
