from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CertificateResponse(BaseModel):
    id: UUID
    user_id: UUID
    course_id: UUID
    certificate_number: str
    issued_at: datetime
    pdf_url: Optional[str] = None
    verification_hash: str
    metadata_: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)
