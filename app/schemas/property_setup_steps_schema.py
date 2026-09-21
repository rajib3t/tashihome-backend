from typing import Dict, List
from pydantic import BaseModel

from app.schemas.response import BaseResponse


class PropertySetupStepsData(BaseModel):
    steps: Dict[str, bool]
    completed_steps: List[str]
    percent_complete: int
    is_complete: bool


class PropertySetupStepsResponseSchema(BaseResponse):
    data: PropertySetupStepsData

