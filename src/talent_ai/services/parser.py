"""Structured resume parsing for plain text input."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from talent_ai.domain import Candidate, new_id, normalize_skills


class ResumeParseError(ValueError):
    """Raised when resume text cannot be read or contains no usable fields."""


SKILLS: tuple[str, ...] = (
    "machine learning",
    "deep learning",
    "data analysis",
    "project management",
    "product management",
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "vue",
    "node.js",
    "fastapi",
    "django",
    "flask",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "docker",
    "kubernetes",
    "terraform",
    "aws",
    "azure",
    "gcp",
    "git",
    "ci/cd",
    "linux",
    "pytest",
    "unit testing",
    "communication",
    "leadership",
    "agile",
    "scrum",
    "rest api",
    "graphql",
    "excel",
    "tableau",
    "power bi",
)

LOCATIONS: tuple[str, ...] = (
    "beijing",
    "shanghai",
    "shenzhen",
    "hangzhou",
    "guangzhou",
    "chengdu",
    "nanjing",
    "wuhan",
    "remote",
    "new york",
    "san francisco",
    "london",
    "singapore",
    "tokyo",
    "berlin",
)

EDUCATION_MARKERS: tuple[str, ...] = (
    "bachelor",
    "master",
    "phd",
    "doctorate",
    "b.s.",
    "m.s.",
    "b.eng",
    "m.eng",
    "university",
    "college",
)

_EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
_PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}"
)
_YEARS_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:\+\s*)?years?(?:\s+of)?(?:\s+experience)?",
    re.IGNORECASE,
)
_YEAR_RANGE_PATTERN = re.compile(r"(20\d{2})\s*[-–]\s*(20\d{2})")


@dataclass(frozen=True)
class ParsedResume:
    """Normalized fields extracted from resume text."""

    name: str
    email: str
    phone: str = ""
    location: str = ""
    years_experience: float = 0.0
    skills: tuple[str, ...] = field(default_factory=tuple)
    education: str = ""

    def to_candidate(self, *, resume_text: str, candidate_id: str | None = None) -> Candidate:
        return Candidate(
            id=candidate_id or new_id("candidate"),
            name=self.name,
            email=self.email,
            phone=self.phone,
            location=self.location,
            years_experience=self.years_experience,
            skills=self.skills,
            education=self.education,
            resume_text=resume_text.strip(),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "location": self.location,
            "years_experience": self.years_experience,
            "skills": list(self.skills),
            "education": self.education,
        }


class ResumeParser:
    """Extract normalized candidate fields from plain-text resumes."""

    def __init__(
        self,
        *,
        skills: Iterable[str] = SKILLS,
        locations: Iterable[str] = LOCATIONS,
    ) -> None:
        self.skills = tuple(normalize_skills(skills))
        self.locations = tuple(item.strip().lower() for item in locations)
        self.skill_phrases = tuple(skill for skill in self.skills if " " in skill)
        self.skill_tokens = tuple(skill for skill in self.skills if " " not in skill)

    def parse_text(self, text: str) -> ParsedResume:
        if not text or not text.strip():
            raise ResumeParseError("resume text is empty")
        normalized = re.sub(r"\r\n?", "\n", text).strip()
        return ParsedResume(
            name=self._extract_name(normalized),
            email=self._extract_email(normalized),
            phone=self._extract_phone(normalized),
            location=self._extract_location(normalized),
            years_experience=self._extract_years_experience(normalized),
            skills=self._extract_skills(normalized),
            education=self._extract_education(normalized),
        )

    def parse_file(self, path: str | Path) -> ParsedResume:
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            raise ResumeParseError(f"cannot read resume file: {exc}") from exc
        except UnicodeDecodeError as exc:
            raise ResumeParseError("resume file is not valid UTF-8 text") from exc
        return self.parse_text(text)

    def parse_bytes(self, data: bytes) -> ParsedResume:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ResumeParseError("resume bytes are not valid UTF-8 text") from exc
        return self.parse_text(text)

    def _extract_name(self, text: str) -> str:
        ignored_prefixes = ("resume", "curriculum", "cv")
        for line in text.splitlines():
            candidate = line.strip(" |#-")
            if not candidate:
                continue
            if "@" in candidate or _PHONE_PATTERN.fullmatch(candidate):
                continue
            if candidate.lower().startswith(ignored_prefixes):
                continue
            if len(candidate) <= 80:
                return candidate
        return ""

    def _extract_email(self, text: str) -> str:
        match = _EMAIL_PATTERN.search(text)
        return match.group(0).lower() if match else ""

    def _extract_phone(self, text: str) -> str:
        match = _PHONE_PATTERN.search(text)
        if not match:
            return ""
        digits = re.sub(r"\D", "", match.group(0))
        return match.group(0).strip() if len(digits) >= 7 else ""

    def _extract_location(self, text: str) -> str:
        lowered = text.lower()
        for location in sorted(self.locations, key=len, reverse=True):
            if location in lowered:
                return location
        return ""

    def _extract_years_experience(self, text: str) -> float:
        lowered = text.lower()
        direct = _YEARS_PATTERN.search(lowered)
        if direct:
            return float(direct.group(1))
        range_match = _YEAR_RANGE_PATTERN.search(lowered)
        if range_match:
            start, end = int(range_match.group(1)), int(range_match.group(2))
            if end >= start:
                return float(max(0, end - start))
        return 0.0

    def _extract_skills(self, text: str) -> tuple[str, ...]:
        normalized = re.sub(r"[^a-z0-9+#. /-]", " ", text.lower())
        normalized = re.sub(r"\s+", " ", normalized)
        found: set[str] = set()
        for phrase in self.skill_phrases:
            if phrase in normalized:
                found.add(phrase)
        tokens = set(re.split(r"\s+", normalized))
        found.update(token for token in self.skill_tokens if token in tokens)
        return normalize_skills(found)

    def _extract_education(self, text: str) -> str:
        for line in text.splitlines():
            lowered = line.lower()
            if any(marker in lowered for marker in EDUCATION_MARKERS):
                return line.strip()
        return ""

