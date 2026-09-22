from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.response import BaseResponse, PaginationResponse


class AgreementTemplateClauseSchema(BaseModel):
    heading: str
    body: str

    model_config = ConfigDict(from_attributes=True)


class AgreementTemplateSchema(BaseModel):
    id: Optional[str] = None
    name: str
    version: str
    description: Optional[str] = None
    template_type: str
    status: str
    is_default: bool
    content_json: Optional[str] = None   # raw JSON string; frontend parses
    pdf_file_key: Optional[str] = None   # storage key — resolved to URL in response
    pdf_url: Optional[str] = None        # resolved public/signed URL (if pdf_upload)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_url(cls, template, pdf_url: Optional[str] = None) -> "AgreementTemplateSchema":
        from uuid import UUID as _UUID
        pid = template.public_id
        return cls(
            id=str(pid) if pid else None,
            name=template.name,
            version=template.version,
            description=template.description,
            template_type=template.template_type.value if hasattr(template.template_type, "value") else str(template.template_type),
            status=template.status.value if hasattr(template.status, "value") else str(template.status),
            is_default=bool(template.is_default),
            content_json=template.content_json,
            pdf_file_key=template.pdf_file_key,
            pdf_url=pdf_url,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )


class AgreementTemplateSummarySchema(BaseModel):
    id: Optional[str] = None
    name: str
    version: str
    template_type: str
    status: str
    is_default: bool

    model_config = ConfigDict(from_attributes=True)


class AgreementTemplateResponseSchema(BaseResponse):
    data: AgreementTemplateSchema


class AgreementTemplateListResponseSchema(PaginationResponse):
    data: List[AgreementTemplateSchema]

