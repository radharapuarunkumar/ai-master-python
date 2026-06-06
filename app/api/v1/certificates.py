import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user, get_db
from app.models.certificate import Certificate
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
    result = await db.execute(select(Certificate).where(Certificate.user_id == current_user.id))
    certs = result.scalars().all()
    return ResponseEnvelope(data=[CertificateResponse.model_validate(c) for c in certs])


@router.post("/{course_id}", response_model=ResponseEnvelope[CertificateResponse])
async def generate_certificate(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[CertificateResponse]:
    """Generate a certificate for a course."""
    # Check if already exists
    result = await db.execute(
        select(Certificate)
        .where(Certificate.user_id == current_user.id)
        .where(Certificate.course_id == course_id)
    )
    cert = result.scalars().first()
    if not cert:
        cert = Certificate(
            user_id=current_user.id,
            course_id=course_id,
            certificate_number=f"CERT-{uuid.uuid4().hex[:8].upper()}",
            verification_hash=uuid.uuid4().hex
        )
        db.add(cert)
        await db.commit()
        await db.refresh(cert)
        
    return ResponseEnvelope(data=CertificateResponse.model_validate(cert))
