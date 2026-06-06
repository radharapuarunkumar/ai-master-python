import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.certificate import CertificateResponse
from app.schemas.common import ResponseEnvelope

router = APIRouter(prefix="/certificates", tags=["Certificates"])

@router.get("", response_model=ResponseEnvelope[list[CertificateResponse]])
async def list_certificates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[list[CertificateResponse]]:
    """List user's certificates."""
    cert = CertificateResponse(
        id=uuid.uuid4(),
        user_id=current_user.id,
        course_id=uuid.uuid4(),
        certificate_number=f"CERT-{uuid.uuid4().hex[:8].upper()}",
        issued_at=datetime.now(timezone.utc),
        pdf_url="https://example.com/certificate.pdf",
        verification_hash=uuid.uuid4().hex,
        metadata_={"grade": "A+"}
    )
    return ResponseEnvelope(data=[cert])


@router.post("/{course_id}", response_model=ResponseEnvelope[CertificateResponse])
async def generate_certificate(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[CertificateResponse]:
    """Generate a certificate for a course."""
    cert = CertificateResponse(
        id=uuid.uuid4(),
        user_id=current_user.id,
        course_id=course_id,
        certificate_number=f"CERT-{uuid.uuid4().hex[:8].upper()}",
        issued_at=datetime.now(timezone.utc),
        pdf_url="https://example.com/certificate.pdf",
        verification_hash=uuid.uuid4().hex,
        metadata_={"grade": "A+"}
    )
    return ResponseEnvelope(data=cert)
