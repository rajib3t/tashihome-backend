import pytest
from app.application.dto.properties.property import PropertyDTO, PropertyUpdateDTO
from app.core.exceptions import AppException


def test_property_dto_accepts_valid_description_within_150_words():
    words = ["word"] * 150
    valid_desc = " ".join(words)
    dto = PropertyDTO(
        name="Cozy Himalayan Cottage",
        description=valid_desc,
    )
    assert dto.description == valid_desc


def test_property_dto_rejects_description_exceeding_150_words():
    words = ["word"] * 151
    invalid_desc = " ".join(words)
    with pytest.raises(AppException) as exc_info:
        PropertyDTO(
            name="Cozy Himalayan Cottage",
            description=invalid_desc,
        )
    assert exc_info.value.status_code == 422
    assert "must not exceed 150 words" in exc_info.value.message
    assert exc_info.value.error_code == "DESCRIPTION_TOO_MANY_WORDS"


def test_property_dto_accepts_none_and_empty_description():
    dto_none = PropertyDTO(name="Cozy Himalayan Cottage", description=None)
    assert dto_none.description is None

    dto_empty = PropertyDTO(name="Cozy Himalayan Cottage", description="   ")
    assert dto_empty.description is None


def test_property_dto_rejects_dangerous_patterns_in_description():
    with pytest.raises(AppException) as exc_info:
        PropertyDTO(
            name="Cozy Himalayan Cottage",
            description="Nice stay <script>alert('xss')</script>",
        )
    assert exc_info.value.status_code == 422
    assert exc_info.value.error_code == "DESCRIPTION_INVALID"


def test_property_update_dto_validates_150_words():
    words = ["homestay"] * 150
    dto = PropertyUpdateDTO(description=" ".join(words))
    assert dto.description == " ".join(words)

    with pytest.raises(AppException) as exc_info:
        PropertyUpdateDTO(description=" ".join(["homestay"] * 151))
    assert exc_info.value.status_code == 422
    assert "must not exceed 150 words" in exc_info.value.message
