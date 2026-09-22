from typing import Optional
from pydantic import BaseModel, ConfigDict


class CreateAgreementTemplateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    version: str = "1.0"
    description: Optional[str] = None
    template_type: str = "rich_text"      # "rich_text" | "pdf_upload"
    content_json: Optional[str] = None    # JSON string of clauses array
    status: str = "draft"                 # "draft" | "active"


class UpdateAgreementTemplateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    template_type: Optional[str] = None
    content_json: Optional[str] = None
    status: Optional[str] = None


class AgreementTemplateQueryDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    page: int = 1
    size: int = 20
    limit: Optional[int] = None
    status: Optional[str] = None
    search: Optional[str] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"

    def model_post_init(self, __context: object) -> None:
        if self.limit is not None and self.limit > 0:
            self.size = self.limit

