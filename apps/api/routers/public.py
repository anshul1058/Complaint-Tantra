from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models import CaseAction, Institution
from schemas import PublicComplaintCreate, PublicComplaintOut
from services.case_service import create_case

router = APIRouter(prefix="/public", tags=["public"])


@router.post(
    "/complaints",
    response_model=PublicComplaintOut,
    status_code=status.HTTP_201_CREATED,
)
async def register_public_complaint(
    body: PublicComplaintCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PublicComplaintOut:
    """Register a citizen complaint and run the normal AI triage pipeline."""
    from routers.ingest import _post_ingest

    complaint_text = (
        f"Subject: {body.subject}\n\n{body.description}\n\n"
        f"Incident date: {body.incident_date or 'Not provided'}\n"
        f"Relief sought: {body.relief_sought or 'Not provided'}\n"
        f"Supporting details: {body.supporting_details or 'Not provided'}"
    )
    case = await create_case(db, {
        # Keep public intake distinguishable while routing it to PGRC. The
        # case/queue scope exposes public intake to every officer for triage.
        "source_bureau": "PUBLIC",
        "assigned_bureau": "PGRC",
        "raw_institution": body.college_name,
        "complainant_type": body.complainant_type,
        "category": body.category,
        "subcategory": body.subcategory,
        "text_original": complaint_text,
        "text_english": complaint_text if body.language.lower() == "english" else None,
        "language": body.language,
    })

    await _post_ingest(db, case)

    if case.institution_id:
        institution = await db.get(Institution, case.institution_id)
        if institution:
            institution.address = body.college_address
            institution.city = body.college_city
            institution.state = body.college_state
            institution.permanent_id = body.college_permanent_id or institution.permanent_id
            institution.trust_or_society = body.college_affiliation

    db.add(CaseAction(
        case_id=case.id,
        actor_type="public",
        action="complaint_submitted",
        remarks="Complaint registered through the public grievance form.",
        payload={
            "complainant_name": body.complainant_name,
            "complainant_email": body.complainant_email,
            "complainant_phone": body.complainant_phone,
            "college_permanent_id": body.college_permanent_id,
            "college_pincode": body.college_pincode,
        },
    ))
    await db.commit()

    return PublicComplaintOut(
        case_id=case.id,
        case_no=case.case_no,
        status=case.status,
        assigned_bureau=case.assigned_bureau,
        message="Complaint registered and sent for AI-assisted triage.",
    )
