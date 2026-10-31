"""Seed a small, realistic demo dataset (users, SLA, cases, overlaps).

Usage:
    cd apps/api && python seed.py && python seed_demo.py

Safe to re-run: existing case numbers are skipped.
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from db import SessionLocal, init_db
from models import Case, User
from routers.ingest import _post_ingest
from services.case_service import create_case
from seed import seed as seed_base

DEMO_CASES = [
    ("CT-DEMO-001", "Apex Institute of Technology & Management, Greater Noida", "RB", "fraud",
     "The college admitted 120 B.Tech AI-ML students without AICTE approval and threatened "
     "students with mark deduction if anyone complains.", "student", 9),
    ("CT-DEMO-002", "Apex Institute of Technology & Management, Greater Noida", "PGRC", "fees",
     "My fee refund was denied after I cancelled admission. The college keeps the Rs 1.8 lakh "
     "tuition fee and refuses to respond.", "parent", 7),
    ("CT-DEMO-003", "Vidyapeeth College of Engineering & Research, Pune", "RB", "faculty",
     "The mechanical department has only two faculty members for four semesters of students.", "student", 14),
    ("CT-DEMO-004", "Vidyapeeth College of Engineering & Research, Pune", "PGRC", "fees",
     "Capitation fee was demanded in cash during admission and no receipt was issued.", "parent", 12),
    ("CT-DEMO-005", "Kalinga Polytechnic & Technical Campus, Bhubaneswar", "PGRC", "safety",
     "Seniors are ragging first-year students in the hostel and threatening them with violence.",
     "student", 3),
    ("CT-DEMO-006", "Sahyadri Institute of Pharmaceutical Sciences, Mangaluru", "RB", "certificate",
     "My degree certificate has not been issued for eight months despite repeated requests.",
     "student", 25),
    ("CT-DEMO-007", "Apex Institute of Technology & Management, Greater Noida", "OTHER", "safety",
     "Faculty members are harassing a student who reported the unapproved course, and the "
     "student has threatened self harm.", "other", 2),
    ("CT-DEMO-008", "Government Polytechnic, Diglipur", "RB", "infrastructure",
     "The laboratory equipment is broken and the hostel building is unsafe for students.",
     "student", 18),
    ("CT-DEMO-009", "Government Polytechnic, Diglipur", "PGRC", "examination",
     "Exam results have been withheld for two months and revaluation requests are ignored.",
     "student", 20),
    ("CT-DEMO-010", "Dr. B.R. Ambedkar Institute of Technology, Port Blair", "RB", "placement",
     "The placement cell promised jobs but no company visited the campus this year.", "student", 30),
]


async def seed_demo() -> None:
    await init_db()
    await seed_base()

    async with SessionLocal() as db:
        officers = {
            u.bureau: u for u in (await db.execute(
                select(User).where(User.role == "officer")
            )).scalars()
        }
        now = datetime.now(timezone.utc)
        created = 0
        for case_no, institution, bureau, category, text, complainant, days_ago in DEMO_CASES:
            existing = (await db.execute(select(Case).where(Case.case_no == case_no))).scalar_one_or_none()
            if existing:
                continue
            case = await create_case(db, {
                "case_no": case_no,
                "raw_institution": institution,
                "source_bureau": bureau,
                "assigned_bureau": bureau,
                "category": category,
                "complainant_type": complainant,
                "text_original": text,
                "language": "en",
                "received_at": now - timedelta(days=days_ago),
            })
            officer = officers.get(bureau)
            if officer:
                case.assigned_officer = officer.id
            await db.commit()
            await _post_ingest(db, case)
            created += 1

    print(f"Seeded {created} demo cases (existing case numbers skipped).")


if __name__ == "__main__":
    sys.exit(asyncio.run(seed_demo()))
