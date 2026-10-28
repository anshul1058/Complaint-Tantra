import csv
import io
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from auth import ROLE_AUTHORITY, ROLE_SENIOR, require_roles
from db import get_db
from models import User
from services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])

ReportType = Literal["institution", "bureau", "region", "ageing", "disposal"]


@router.get("/{report_type}")
async def get_report(
    report_type: ReportType,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(ROLE_SENIOR, ROLE_AUTHORITY, "admin"))],
    format: Literal["json", "csv"] = "json",
) -> Response:
    """Numbers always from SQL; LLM writes narrative only (§6.6). PDF export deferred."""
    if report_type == "institution":
        data = await report_service.institution_leaderboard(db)
    elif report_type == "bureau":
        data = await report_service.by_bureau(db)
    elif report_type == "region":
        data = await report_service.by_region(db)
    elif report_type == "ageing":
        data = await report_service.ageing(db)
    else:
        data = await report_service.disposal(db)

    if format == "csv":
        buf = io.StringIO()
        if data:
            writer = csv.DictWriter(buf, fieldnames=list(data[0].keys()))
            writer.writeheader()
            writer.writerows(data)
        return Response(
            content=buf.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{report_type}.csv"'},
        )
    import json

    return Response(content=json.dumps(data, default=str), media_type="application/json")
