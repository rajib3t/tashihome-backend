from pydantic import BaseModel, Field


class AdminDashboardQueryDTO(BaseModel):
    months: int = Field(default=12, ge=1, le=24, description="Number of months for trend analytics")

