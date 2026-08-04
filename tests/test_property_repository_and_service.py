from app.repositories.property_repository import PropertyRepository
from app.services.property_service import PropertyService


def test_property_repository_and_service_are_available():
    assert PropertyRepository.__name__ == "PropertyRepository"
    assert hasattr(PropertyService, "create")
    assert hasattr(PropertyService, "list")
