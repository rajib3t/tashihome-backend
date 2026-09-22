import enum
import uuid

from sqlalchemy import (
    UUID,
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class AgreementType(str, enum.Enum):
    HOST_ONBOARDING = "host_onboarding"
    COMMISSION_AGREEMENT = "commission_agreement"
    SUPPLEMENTAL = "supplemental"


class AgreementStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    PARTIALLY_SIGNED = "partially_signed"
    SIGNED = "signed"
    DECLINED = "declined"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class VendorAgreement(Base):
    __tablename__ = "vendor_agreements"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )

    vendor_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    host_request_id = Column(
        BigInteger,
        ForeignKey("host_requests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    agreement_type = Column(
        Enum(
            AgreementType,
            values_callable=lambda x: [e.value for e in x],
            name="agreementtype",
        ),
        default=AgreementType.HOST_ONBOARDING,
        nullable=False,
        index=True,
    )

    title = Column(String(255), nullable=False)
    version = Column(String(50), default="1.0", nullable=False)
    status = Column(
        Enum(
            AgreementStatus,
            values_callable=lambda x: [e.value for e in x],
            name="agreementstatus",
        ),
        default=AgreementStatus.SENT,
        nullable=False,
        index=True,
    )

    token = Column(String(255), unique=True, nullable=False, index=True)
    commission_percentage = Column(Numeric(5, 2), default=10.0, nullable=False)

    expires_at = Column(DateTime(timezone=True), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    viewed_at = Column(DateTime(timezone=True), nullable=True)

    # First Party (Platform Operator / TashiHome) Execution Record
    first_party_signer_name = Column(String(255), nullable=True)
    first_party_signer_role = Column(String(100), nullable=True, default="Platform Authorized Signatory")
    first_party_signature_type = Column(String(50), nullable=True, default="digital")
    first_party_signature_data = Column(Text, nullable=True)
    first_party_signature_font = Column(String(100), nullable=True)
    first_party_signed_at = Column(DateTime(timezone=True), nullable=True)
    first_party_signer_ip = Column(String(100), nullable=True)

    # Second Party (Homestay Host / Vendor) Execution Record
    signed_at = Column(DateTime(timezone=True), nullable=True)
    signer_name = Column(String(255), nullable=True)
    signer_email = Column(String(255), nullable=True)
    signer_phone = Column(String(50), nullable=True)
    signature_type = Column(String(50), nullable=True)  # 'typed' or 'drawn'
    signature_data = Column(Text, nullable=True)  # base64 data URL or typed text
    signature_font = Column(String(100), nullable=True)  # chosen font key/name for typed signature
    signer_ip = Column(String(100), nullable=True)
    signer_user_agent = Column(String(500), nullable=True)

    document_hash = Column(String(64), nullable=True)  # SHA-256
    pdf_file_url = Column(String(500), nullable=True)
    terms_snapshot = Column(Text, nullable=True)  # JSON or text of terms/clauses

    created_by = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    template_id = Column(
        BigInteger,
        ForeignKey("agreement_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )


    @property
    def is_first_party_signed(self) -> bool:
        return self.first_party_signed_at is not None

    @property
    def is_second_party_signed(self) -> bool:
        return self.signed_at is not None

    @property
    def is_bilateral_signed(self) -> bool:
        return self.is_first_party_signed and self.is_second_party_signed

    @property
    def second_party_signer_name(self) -> str | None:
        return self.signer_name

    @property
    def second_party_signed_at(self):
        return self.signed_at

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    vendor = relationship("User", foreign_keys=[vendor_id], back_populates="agreements")
    host_request = relationship("HostRequest", foreign_keys=[host_request_id], back_populates="agreements")
    creator = relationship("User", foreign_keys=[created_by])
    template = relationship("AgreementTemplate", foreign_keys=[template_id], back_populates="agreements")


