from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class IntakeEntities(BaseModel):
    model_config = ConfigDict(extra="forbid")

    institution_name: str | None = None
    city: str | None = None
    state: str | None = None
    people_roles: list[str] = Field(default_factory=list)
    amounts: list[str] = Field(default_factory=list)
    dates: list[str] = Field(default_factory=list)
    documents_mentioned: list[str] = Field(default_factory=list)


class IntakeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: str | None = None
    text_english: str | None = None
    category: str | None = None
    subcategory: str | None = None
    entities: IntakeEntities = Field(default_factory=IntakeEntities)
    summary: str | None = None
    needs_review: bool = False
    source: str | None = None


class Emotion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: Literal[
        "distress",
        "fear",
        "anger",
        "frustration",
        "hopelessness",
        "neutral",
        "hopeful",
    ] = "neutral"
    intensity: float = Field(ge=0.0, le=1.0, default=0.2)


class TriageOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criticality: Literal["C1", "C2", "C3", "C4"] = "C4"
    criticality_reason: str | None = None
    emotion: Emotion = Field(default_factory=Emotion)
    safety_flag: bool = False
    flag_reason: str | None = None
    urgency_cues: list[str] = Field(default_factory=list)
    needs_review: bool = False
    source: str | None = None


class OverlapJudge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    same_institution: bool | None = None
    same_issue: bool | None = None
    related: Literal["same_issue", "related_issue", "different_issue", "duplicate"] | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    reason: str | None = Field(default=None, max_length=80)


class WebFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    title: str | None = None
    source_name: str | None = None
    published_at: str | None = None
    summary: str | None = None
    topic: Literal["fees", "safety", "accreditation", "faculty", "fraud", "placement", "court", "other"] = "other"
    sentiment: Literal["negative", "neutral", "positive"] = "neutral"
    emotion_label: str | None = None
    severity: float = Field(ge=0.0, le=1.0, default=0.0)
    match_confidence: float = Field(ge=0.0, le=1.0, default=0.0)


class WebIntelOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    findings: list[WebFinding] = Field(default_factory=list)
    reputation_summary: str | None = None
    reputation_risk: float = Field(ge=0.0, le=100.0, default=0.0)
    unverified: list[str] = Field(default_factory=list)
    needs_review: bool = False
    source: str | None = None


class AgentRunMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str | None = None
    prompt_version: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    latency_ms: int | None = None
