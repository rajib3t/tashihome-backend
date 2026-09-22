import enum
import uuid

from sqlalchemy import (
    UUID,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class AgreementTemplateType(str, enum.Enum):
    RICH_TEXT = "rich_text"
    PDF_UPLOAD = "pdf_upload"


class AgreementTemplateStatus(str, enum.Enum):
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"


class AgreementTemplate(Base):
    __tablename__ = "agreement_templates"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )

    name = Column(String(255), nullable=False)
    version = Column(String(50), default="1.0", nullable=False)
    description = Column(Text, nullable=True)

    template_type = Column(
        Enum(
            AgreementTemplateType,
            values_callable=lambda x: [e.value for e in x],
            name="agreementtemplatetype",
        ),
        default=AgreementTemplateType.RICH_TEXT,
        nullable=False,
        index=True,
    )

    status = Column(
        Enum(
            AgreementTemplateStatus,
            values_callable=lambda x: [e.value for e in x],
            name="agreementtemplatestatus",
        ),
        default=AgreementTemplateStatus.DRAFT,
        nullable=False,
        index=True,
    )

    # JSON array of clauses: [{"heading": "...", "body": "..."}]
    # Used when template_type == rich_text
    content_json = Column(Text, nullable=True)

    # S3/storage key for uploaded PDF document
    # Used when template_type == pdf_upload
    pdf_file_key = Column(String(500), nullable=True)

    # Only one template can be default at a time
    is_default = Column(Boolean, default=False, nullable=False, index=True)

    created_by = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    agreements = relationship("VendorAgreement", back_populates="template", foreign_keys="VendorAgreement.template_id")

