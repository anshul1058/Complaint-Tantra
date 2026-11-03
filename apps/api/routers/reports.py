import csv
import io
import json
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth import ROLE_ADMIN, ROLE_AUTHORITY, ROLE_SENIOR, require_roles
from db import get_db
from models import User
from services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])

ReportType = Literal[
    "institution", "bureau", "region", "ageing", "disposal",
    "status", "duplicates", "performance", "monthly",
]


async def _load(report_type: str, db: AsyncSession):
    loaders = {
        "institution": report_service.institution_leaderboard,
        "bureau": report_service.by_bureau,
        "region": report_service.by_region,
        "ageing": report_service.ageing,
        "disposal": report_service.disposal,
        "status": report_service.status_wise,
        "duplicates": report_service.duplicates,
        "performance": report_service.performance,
        "monthly": report_service.monthly,
    }
    return await loaders[report_type](db)


def _csv(rows: list[dict]) -> bytes:
    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return buf.getvalue().encode()


def _pdf(title: str, rows: list[dict]) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
    except Exception:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "PDF export requires reportlab")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    headers = list(rows[0].keys()) if rows else ["message"]
    data = [headers] + [[str(r.get(h, "")) for h in headers] for r in rows]
    if not rows:
        data.append(["No data"])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    doc.build([Paragraph(f"AICTE Complaint-Tantra — {title}", styles["Title"]), table])
    return buf.getvalue()


@router.get("/{report_type}")
async def get_report(
    report_type: ReportType,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(ROLE_SENIOR, ROLE_AUTHORITY, ROLE_ADMIN))],
    format: Literal["json", "csv", "pdf"] = "json",
) -> Response:
    """Numbers always from SQL; LLM writes narrative only (§6.6)."""
    data = await _load(report_type, db)
    if format == "csv":
        return Response(
            content=_csv(data),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{report_type}.csv"'},
        )
    if format == "pdf":
        return Response(
            content=_pdf(report_type, data),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{report_type}.pdf"'},
        )
    return Response(content=json.dumps(data, default=str), media_type="application/json")
