import csv
import io
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from agents import detect_overlaps, run_intake, run_triage
from auth import ROLE_ADMIN, ROLE_OFFICER, require_roles
from db import SessionLocal, get_db
from models import Alert, Case, Institution, User
from schemas import CaseCreate, CaseOut, IngestRequest
from services import case_service, priority as priority_service
from services.case_service import create_case, resolve_institution, sla_days_for
from services.entity_resolution import normalize_name, verdict
from services.sla_engine import time_pressure

router = APIRouter(prefix="/ingest", tags=["ingest"])


async def _post_ingest(db: AsyncSession, case: Case) -> None:
    """Run agents async (§7): intake → triage → priority → overlaps. AI never sets status."""
    case_dict = {
        "case_no": case.case_no,
        "raw_institution": case.raw_institution,
        "text_original": case.text_original,
        "text_english": case.text_english,
        "language": case.language,
        "category": case.category,
        "complainant_type": case.complainant_type,
    }
    intake = await run_intake(db, case.id, case_dict)
    triage = await run_triage(db, case.id, case_dict, intake)

    if intake.get("category") and not case.category:
        case.category = intake["category"]
    if intake.get("subcategory") and not case.subcategory:
        case.subcategory = intake["subcategory"]
    if intake.get("text_english") and not case.text_english:
        case.text_english = intake["text_english"]
    if intake.get("language") and not case.language:
        case.language = intake["language"]
    if intake.get("summary"):
        case.ai_summary = intake["summary"]
    case.ai_version = f"rules-{intake.get('source', 'rules')}"
    # Triage may only suggest fields — never status (§7)
    case.criticality = triage.get("criticality") or case.criticality
    case.emotion_label = (triage.get("emotion") or {}).get("label") or case.emotion_label
    case.emotion_intensity = (triage.get("emotion") or {}).get("intensity") or case.emotion_intensity

    # Institution resolution (§5)
    if case.raw_institution and case.institution_id is None:
        inst, score = await resolve_institution(db, name=case.raw_institution)
        if inst is None and verdict(score) == "new":
            norm = normalize_name(case.raw_institution)
            inst = Institution(name=case.raw_institution, name_normalized=norm)
            db.add(inst)
            await db.flush()
        elif inst is not None and score < 0.70:
            inst = None
        case.institution_id = inst.id if inst else None

    links = await detect_overlaps(db, case)

    risk_idx = None
    if case.institution_id:
        from services.risk import compute_risk

        risk_row = await compute_risk(db, case.institution_id)
        risk_idx = risk_row.risk_index

    days, _ = await sla_days_for(db, case.category)
    tp = time_pressure(datetime.now(timezone.utc), case.received_at, case.expected_disposal, days)
    safety = bool(triage.get("safety_flag"))
    score, reasons = priority_service.compute_priority(
        criticality=case.criticality,
        emotion_label=case.emotion_label,
        emotion_intensity=case.emotion_intensity,
        time_pressure=tp,
        institution_risk_index=risk_idx,
        links=links,
        safety_flag=safety,
    )
    case.priority_score = score
    case.priority_reasons = reasons
    await db.commit()

    if safety:
        db.add(Alert(
            kind="safety_flag",
            case_id=case.id,
            institution_id=case.institution_id,
            severity="critical",
            message=f"Safety flag on {case.case_no}: urgent human review",
            target_role="authority",
        ))
        await db.commit()
    for link in links:
        if link.get("tier") in ("T1", "T2"):
            db.add(Alert(
                kind="overlap",
                case_id=case.id,
                severity="high" if link.get("tier") == "T1" else "medium",
                message=f"{link.get('tier')} overlap detected for {case.case_no} (conf {link.get('confidence')})",
                target_role="officer",
            ))
    await db.commit()


@router.post("/cases", response_model=list[CaseOut], status_code=status.HTTP_201_CREATED)
async def ingest_cases(
    body: IngestRequest | CaseCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(ROLE_ADMIN, ROLE_OFFICER))],
) -> list[CaseOut]:
    items = body.cases if isinstance(body, IngestRequest) else [body]
    if not items:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No cases provided")
    created: list[Case] = []
    for item in items:
        data = item.model_dump()
        if data.get("case_no"):
            from sqlalchemy import select

            existing = (await db.execute(select(Case).where(Case.case_no == data["case_no"]))).scalar_one_or_none()
            if existing:
                created.append(existing)
                continue
        case = await create_case(db, data)
        await _post_ingest(db, case)
        created.append(case)
    return [CaseOut.model_validate(c) for c in created]


@router.post("/cases/csv", response_model=list[CaseOut], status_code=status.HTTP_201_CREATED)
async def ingest_csv(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(ROLE_ADMIN, ROLE_OFFICER))],
) -> list[CaseOut]:
    raw = await request.body()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "CSV must be UTF-8")
    reader = csv.DictReader(io.StringIO(text))
    created = []
    for row in reader:
        data = {k.strip(): (v.strip() if v else None) for k, v in row.items() if k}
        payload = CaseCreate(**{k: v for k, v in data.items() if k in CaseCreate.model_fields})
        case = await create_case(db, payload.model_dump())
        await _post_ingest(db, case)
        created.append(case)
    return [CaseOut.model_validate(c) for c in created]
