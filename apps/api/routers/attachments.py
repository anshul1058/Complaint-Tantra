"""Case attachments (FR-13 P2) stored on local disk for demo deployments."""

import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import can_see_full_case, get_current_user
from config import REPO_ROOT
from db import get_db
from models import Attachment, Case, User
from schemas import AttachmentOut
from services.audit import add_event

router = APIRouter(prefix="/cases/{case_id}/attachments", tags=["attachments"])
UPLOAD_DIR = REPO_ROOT / "data" / "uploads"
MAX_BYTES = 10 * 1024 * 1024


async def _case_for(db: AsyncSession, case_id: uuid.UUID, user: User) -> Case:
    case = await db.get(Case, case_id)
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    if not can_see_full_case(user, case.assigned_bureau):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Out of scope")
    return case


@router.get("", response_model=list[AttachmentOut])
async def list_attachments(
    case_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[AttachmentOut]:
    await _case_for(db, case_id, user)
    rows = (await db.execute(
        select(Attachment).where(Attachment.case_id == case_id).order_by(Attachment.created_at)
    )).scalars().all()
    return [AttachmentOut.model_validate(r) for r in rows]


@router.post("", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    case_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
) -> AttachmentOut:
    await _case_for(db, case_id, user)
    content = await file.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Max 10 MB")
    folder = UPLOAD_DIR / str(case_id)
    folder.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "upload.bin").name
    path = folder / f"{uuid.uuid4().hex}_{safe_name}"
    path.write_bytes(content)
    row = Attachment(
        case_id=case_id,
        filename=safe_name,
        content_type=file.content_type,
        size=len(content),
        path=str(path),
        uploaded_by=user.id,
    )
    db.add(row)
    add_event(db, action="attachment_upload", user=user, entity="case", entity_id=str(case_id),
              meta={"filename": safe_name})
    await db.commit()
    await db.refresh(row)
    return AttachmentOut.model_validate(row)


@router.get("/{attachment_id}/download")
async def download_attachment(
    case_id: uuid.UUID,
    attachment_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> FileResponse:
    await _case_for(db, case_id, user)
    row = await db.get(Attachment, attachment_id)
    if row is None or row.case_id != case_id or not Path(row.path).exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Attachment not found")
    return FileResponse(row.path, filename=row.filename, media_type=row.content_type)


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    case_id: uuid.UUID,
    attachment_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    await _case_for(db, case_id, user)
    row = await db.get(Attachment, attachment_id)
    if row is None or row.case_id != case_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Attachment not found")
    Path(row.path).unlink(missing_ok=True)
    await db.delete(row)
    await db.commit()
