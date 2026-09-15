"""SQLite persistence for candidates, jobs, and match results."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from talent_ai.domain import (
    Candidate,
    Job,
    MatchResult,
    normalize_skills,
    utc_now,
)


SCHEMA = """
CREATE TABLE IF NOT EXISTS candidates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT '',
    years_experience REAL NOT NULL DEFAULT 0,
    skills TEXT NOT NULL DEFAULT '[]',
    education TEXT NOT NULL DEFAULT '',
    resume_text TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    min_years_experience REAL NOT NULL DEFAULT 0,
    required_skills TEXT NOT NULL DEFAULT '[]',
    preferred_skills TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS match_results (
    job_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    score REAL NOT NULL,
    matched_required TEXT NOT NULL DEFAULT '[]',
    missing_required TEXT NOT NULL DEFAULT '[]',
    matched_preferred TEXT NOT NULL DEFAULT '[]',
    reasons TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    PRIMARY KEY (job_id, candidate_id),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_candidates_email
    ON candidates(email);

CREATE INDEX IF NOT EXISTS idx_jobs_title
    ON jobs(title);

CREATE INDEX IF NOT EXISTS idx_match_results_job
    ON match_results(job_id);
"""


def _json_dumps(values: tuple[str, ...]) -> str:
    return json.dumps(list(values), ensure_ascii=False)


def _json_loads(raw: str) -> tuple[str, ...]:
    try:
        data = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return ()
    if not isinstance(data, list):
        return ()
    return normalize_skills(data)


def _json_loads_reasons(raw: str) -> tuple[str, ...]:
    try:
        data = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return ()
    if not isinstance(data, list):
        return ()
    return tuple(str(item) for item in data)


def _candidate_from_row(row: sqlite3.Row) -> Candidate:
    return Candidate.from_dict(
        {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "phone": row["phone"],
            "location": row["location"],
            "years_experience": row["years_experience"],
            "skills": _json_loads(row["skills"]),
            "education": row["education"],
            "resume_text": row["resume_text"],
            "created_at": row["created_at"],
        }
    )


def _job_from_row(row: sqlite3.Row) -> Job:
    return Job.from_dict(
        {
            "id": row["id"],
            "title": row["title"],
            "company": row["company"],
            "location": row["location"],
            "description": row["description"],
            "min_years_experience": row["min_years_experience"],
            "required_skills": _json_loads(row["required_skills"]),
            "preferred_skills": _json_loads(row["preferred_skills"]),
            "created_at": row["created_at"],
        }
    )


def _match_from_row(row: sqlite3.Row) -> MatchResult:
    return MatchResult.from_dict(
        {
            "job_id": row["job_id"],
            "candidate_id": row["candidate_id"],
            "score": row["score"],
            "matched_required": _json_loads(row["matched_required"]),
            "missing_required": _json_loads(row["missing_required"]),
            "matched_preferred": _json_loads(row["matched_preferred"]),
            "reasons": _json_loads_reasons(row["reasons"]),
            "created_at": row["created_at"],
        }
    )


class SqliteRepository:
    """Repository backed by a local SQLite database file."""

    def __init__(self, database_path: str | Path, *, initialize: bool = True) -> None:
        self.database_path = Path(database_path)
        if str(self.database_path) != ":memory:":
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(
            str(self.database_path),
            check_same_thread=False,
        )
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        if initialize:
            self.initialize()

    def initialize(self) -> None:
        """Create tables and indexes when they do not already exist."""

        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "SqliteRepository":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def create_candidate(self, candidate: Candidate) -> Candidate:
        try:
            self.connection.execute(
                """
                INSERT INTO candidates (
                    id, name, email, phone, location, years_experience,
                    skills, education, resume_text, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate.id,
                    candidate.name,
                    candidate.email,
                    candidate.phone,
                    candidate.location,
                    candidate.years_experience,
                    _json_dumps(candidate.skills),
                    candidate.education,
                    candidate.resume_text,
                    candidate.created_at or utc_now(),
                ),
            )
            self.connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"candidate email already exists: {candidate.email}") from exc
        return candidate

    def create_job(self, job: Job) -> Job:
        self.connection.execute(
            """
            INSERT INTO jobs (
                id, title, company, location, description, min_years_experience,
                required_skills, preferred_skills, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.id,
                job.title,
                job.company,
                job.location,
                job.description,
                job.min_years_experience,
                _json_dumps(job.required_skills),
                _json_dumps(job.preferred_skills),
                job.created_at or utc_now(),
            ),
        )
        self.connection.commit()
        return job

    def get_candidate(self, candidate_id: str) -> Candidate | None:
        row = self.connection.execute(
            "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
        ).fetchone()
        return _candidate_from_row(row) if row else None

    def get_job(self, job_id: str) -> Job | None:
        row = self.connection.execute(
            "SELECT * FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()
        return _job_from_row(row) if row else None

    def list_candidates(
        self, *, query: str = "", limit: int = 100, offset: int = 0
    ) -> list[Candidate]:
        like = f"%{query.strip().lower()}%"
        rows = self.connection.execute(
            """
            SELECT * FROM candidates
            WHERE ? = ''
               OR lower(name) LIKE ?
               OR lower(email) LIKE ?
               OR lower(location) LIKE ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (query.strip(), like, like, like, limit, offset),
        ).fetchall()
        return [_candidate_from_row(row) for row in rows]

    def list_jobs(
        self, *, query: str = "", limit: int = 100, offset: int = 0
    ) -> list[Job]:
        like = f"%{query.strip().lower()}%"
        rows = self.connection.execute(
            """
            SELECT * FROM jobs
            WHERE ? = ''
               OR lower(title) LIKE ?
               OR lower(company) LIKE ?
               OR lower(location) LIKE ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (query.strip(), like, like, like, limit, offset),
        ).fetchall()
        return [_job_from_row(row) for row in rows]

    def delete_candidate(self, candidate_id: str) -> bool:
        cursor = self.connection.execute(
            "DELETE FROM candidates WHERE id = ?", (candidate_id,)
        )
        self.connection.commit()
        return cursor.rowcount > 0

    def delete_job(self, job_id: str) -> bool:
        cursor = self.connection.execute(
            "DELETE FROM jobs WHERE id = ?", (job_id,)
        )
        self.connection.commit()
        return cursor.rowcount > 0

    def save_match_results(self, results: list[MatchResult]) -> None:
        if not results:
            return
        self.connection.executemany(
            """
            INSERT OR REPLACE INTO match_results (
                job_id, candidate_id, score, matched_required,
                missing_required, matched_preferred, reasons, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    result.job_id,
                    result.candidate_id,
                    result.score,
                    _json_dumps(result.matched_required),
                    _json_dumps(result.missing_required),
                    _json_dumps(result.matched_preferred),
                    _json_dumps(result.reasons),
                    result.created_at or utc_now(),
                )
                for result in results
            ],
        )
        self.connection.commit()

    def list_match_results(self, job_id: str) -> list[MatchResult]:
        rows = self.connection.execute(
            """
            SELECT * FROM match_results
            WHERE job_id = ?
            ORDER BY score DESC
            """,
            (job_id,),
        ).fetchall()
        return [_match_from_row(row) for row in rows]
