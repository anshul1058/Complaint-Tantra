import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    role: str
    bureau: str | None = None
    region: str | None = None


class CaseCreate(BaseModel):
    case_no: str | None = None
    source_bureau: str = "RB"
    assigned_bureau: str | None = None
    raw_institution: str | None = None
    institution_name: str | None = None
    complainant_type: str | None = None
    category: str | None = None
    subcategory: str | None = None
    text_original: str | None = None
    text_english: str | None = None
    language: str | None = None
    received_at: datetime | None = None


class IngestRequest(BaseModel):
    cases: list[CaseCreate]


class CaseActionRequest(BaseModel):
    action: str  # assigned | transferred | accepted | escalated | deescalated | disposed | reopened | remark | doc_added
    remarks: str | None = None
    payload: dict | None = None


class CaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_no: str
    institution_id: uuid.UUID | None = None
    raw_institution: str | None = None
    source_bureau: str
    assigned_bureau: str
    assigned_officer: uuid.UUID | None = None
    complainant_type: str | None = None
    category: str | None = None
    subcategory: str | None = None
    text_original: str | None = None
    text_english: str | None = None
    language: str | None = None
    status: str
    received_at: datetime
    expected_disposal: datetime | None = None
    last_action_at: datetime | None = None
    next_action: str | None = None
    criticality: str | None = None
    emotion_label: str | None = None
    emotion_intensity: float | None = None
    priority_score: float | None = None
    priority_reasons: dict | None = None
    ai_summary: str | None = None
    ai_version: str | None = None
    overdue: bool = False
    allowed_actions: list[str] = []


class CaseRedactedOut(BaseModel):
    """Cross-bureau overlap view: no text, no AI internals."""

    id: uuid.UUID
    case_no: str
    institution_name: str | None = None
    category: str | None = None
    status: str
    assigned_bureau: str
    assigned_officer: uuid.UUID | None = None
    officer_contact: str | None = None


class ActionOut(BaseModel):
    id: int
    case_id: uuid.UUID
    actor_id: uuid.UUID | None = None
    actor_type: str
    action: str
    from_state: str | None = None
    to_state: str | None = None
    remarks: str | None = None
    payload: dict | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseDetailOut(CaseOut):
    timeline: list[ActionOut] = []
    institution_name: str | None = None
    case_brief: dict | None = None


class LinkDecisionRequest(BaseModel):
    decision: str  # confirmed | rejected


class ManualLinkRequest(BaseModel):
    case_b: uuid.UUID
    tier: str | None = None
    evidence: dict | None = None


class LinkOut(BaseModel):
    id: uuid.UUID
    case_a: uuid.UUID
    case_b: uuid.UUID
    tier: str | None = None
    confidence: float | None = None
    evidence: dict | None = None
    detected_by: str | None = None
    decision: str
    other_case: CaseRedactedOut | None = None

    model_config = ConfigDict(from_attributes=True)


class InstitutionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    permanent_id: str | None = None
    name: str
    name_normalized: str
    address: str | None = None
    city: str | None = None
    state: str | None = None
    region: str | None = None
    trust_or_society: str | None = None
    created_at: datetime


class InstitutionProfileOut(InstitutionOut):
    risk: dict | None = None
    case_count: int = 0
    open_count: int = 0


class WebFindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    title: str | None = None
    source_name: str | None = None
    published_at: datetime | None = None
    retrieved_at: datetime
    summary: str | None = None
    topic: str | None = None
    sentiment: str | None = None
    emotion_label: str | None = None
    severity: float | None = None
    match_confidence: float | None = None


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: str
    case_id: uuid.UUID | None = None
    institution_id: uuid.UUID | None = None
    severity: str | None = None
    message: str
    target_role: str | None = None
    target_user: uuid.UUID | None = None
    created_at: datetime
    acknowledged_at: datetime | None = None


class DashboardSummaryOut(BaseModel):
    total: int = 0
    open: int = 0
    overdue: int = 0
    due_soon: int = 0
    by_status: dict[str, int] = {}
    by_bureau: dict[str, int] = {}
    avg_priority: float | None = None


class WorkloadRow(BaseModel):
    bureau: str
    status: str
    n: int


class HeatmapRow(BaseModel):
    region: str
    n: int


class QueueRow(CaseOut):
    pass


class MetaOptionsOut(BaseModel):
    statuses: list[str]
    transitions: dict[str, list[str]]
    categories: list[dict]
    criticalities: list[str]
    roles: list[str]
    bureaus: list[str]
    complainant_types: list[str]


class ReplayOut(BaseModel):
    case_id: uuid.UUID
    intake: dict | None = None
    triage: dict | None = None
    overlaps: list = []
    priority_score: float | None = None
    needs_review: bool = False


class IntelRefreshOut(BaseModel):
    findings_created: int = 0
    reputation_risk: float | None = None
    needs_review: bool = False
    detail: str | None = None
