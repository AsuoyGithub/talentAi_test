"""Core domain models used by the TalentAI service."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def new_id(prefix: str) -> str:
    """Return a short, readable identifier for a persisted entity."""

    return f"{prefix}_{uuid4().hex[:12]}"


def utc_now() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_skill(value: str) -> str:
    """Normalize a skill label for reliable matching."""

    return " ".join(value.strip().lower().split())


def normalize_skills(values: list[str] | tuple[str, ...] | set[str]) -> tuple[str, ...]:
    """Return a sorted tuple of normalized, non-empty skill labels."""

    unique = {normalize_skill(value) for value in values if value and value.strip()}
    return tuple(sorted(unique))


@dataclass(frozen=True)
class Candidate:
    """A candidate profile derived from a resume or API input."""

    id: str
    name: str
    email: str
    phone: str = ""
    location: str = ""
    years_experience: float = 0.0
    skills: tuple[str, ...] = field(default_factory=tuple)
    education: str = ""
    resume_text: str = ""
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "skills", normalize_skills(self.skills))
        object.__setattr__(self, "years_experience", float(self.years_experience))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Candidate":
        return cls(
            id=str(data["id"]),
            name=str(data.get("name", "")),
            email=str(data.get("email", "")),
            phone=str(data.get("phone", "")),
            location=str(data.get("location", "")),
            years_experience=float(data.get("years_experience", 0.0)),
            skills=normalize_skills(data.get("skills", [])),
            education=str(data.get("education", "")),
            resume_text=str(data.get("resume_text", "")),
            created_at=str(data.get("created_at") or utc_now()),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["skills"] = list(self.skills)
        return data


@dataclass(frozen=True)
class Job:
    """A job requirement used to score candidates."""

    id: str
    title: str
    company: str
    location: str = ""
    description: str = ""
    min_years_experience: float = 0.0
    required_skills: tuple[str, ...] = field(default_factory=tuple)
    preferred_skills: tuple[str, ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "required_skills",
            normalize_skills(self.required_skills),
        )
        object.__setattr__(
            self,
            "preferred_skills",
            normalize_skills(self.preferred_skills),
        )
        object.__setattr__(
            self,
            "min_years_experience",
            float(self.min_years_experience),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Job":
        return cls(
            id=str(data["id"]),
            title=str(data.get("title", "")),
            company=str(data.get("company", "")),
            location=str(data.get("location", "")),
            description=str(data.get("description", "")),
            min_years_experience=float(data.get("min_years_experience", 0.0)),
            required_skills=normalize_skills(data.get("required_skills", [])),
            preferred_skills=normalize_skills(data.get("preferred_skills", [])),
            created_at=str(data.get("created_at") or utc_now()),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["required_skills"] = list(self.required_skills)
        data["preferred_skills"] = list(self.preferred_skills)
        return data


@dataclass(frozen=True)
class MatchResult:
    """An explainable match score between one candidate and one job."""

    job_id: str
    candidate_id: str
    score: float
    matched_required: tuple[str, ...] = field(default_factory=tuple)
    missing_required: tuple[str, ...] = field(default_factory=tuple)
    matched_preferred: tuple[str, ...] = field(default_factory=tuple)
    reasons: tuple[str, ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=utc_now)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MatchResult":
        return cls(
            job_id=str(data["job_id"]),
            candidate_id=str(data["candidate_id"]),
            score=float(data.get("score", 0.0)),
            matched_required=normalize_skills(data.get("matched_required", [])),
            missing_required=normalize_skills(data.get("missing_required", [])),
            matched_preferred=normalize_skills(data.get("matched_preferred", [])),
            reasons=tuple(str(item) for item in data.get("reasons", [])),
            created_at=str(data.get("created_at") or utc_now()),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["matched_required"] = list(self.matched_required)
        data["missing_required"] = list(self.missing_required)
        data["matched_preferred"] = list(self.matched_preferred)
        data["reasons"] = list(self.reasons)
        return data
