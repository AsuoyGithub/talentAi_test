"""Demo data for local evaluation and documentation examples."""

from __future__ import annotations

from talent_ai.domain import Candidate, Job
from talent_ai.storage import SqliteRepository


DEMO_CANDIDATES = (
    Candidate(
        id="candidate_demo_1",
        name="Ada Chen",
        email="ada.chen@example.com",
        phone="+86 138 0000 0001",
        location="shanghai",
        years_experience=6.0,
        skills=("python", "fastapi", "docker", "postgresql", "aws"),
        education="Master of Software Engineering",
        resume_text="Backend engineer with six years of experience in Python and FastAPI.",
    ),
    Candidate(
        id="candidate_demo_2",
        name="Bo Liu",
        email="bo.liu@example.com",
        phone="+86 138 0000 0002",
        location="beijing",
        years_experience=4.0,
        skills=("javascript", "react", "typescript", "node.js", "rest api"),
        education="Bachelor of Computer Science",
        resume_text="Frontend engineer with four years of experience in React and TypeScript.",
    ),
    Candidate(
        id="candidate_demo_3",
        name="Cai Wang",
        email="cai.wang@example.com",
        phone="+86 138 0000 0003",
        location="shanghai",
        years_experience=2.0,
        skills=("python", "sql", "excel", "project management"),
        education="Bachelor of Business Administration",
        resume_text="Data analyst with two years of experience in Python and SQL.",
    ),
)

DEMO_JOBS = (
    Job(
        id="job_demo_1",
        title="Backend Engineer",
        company="Acme AI",
        location="shanghai",
        description="Build scalable Python services and data APIs.",
        min_years_experience=4.0,
        required_skills=("python", "fastapi", "postgresql"),
        preferred_skills=("docker", "aws"),
    ),
    Job(
        id="job_demo_2",
        title="Frontend Engineer",
        company="Acme AI",
        location="beijing",
        description="Build responsive React applications and design systems.",
        min_years_experience=3.0,
        required_skills=("javascript", "react"),
        preferred_skills=("typescript", "node.js"),
    ),
)


def seed_demo_data(repository: SqliteRepository) -> tuple[list[Candidate], list[Job]]:
    """Insert idempotent demo data and return all demo entities."""

    for candidate in DEMO_CANDIDATES:
        if repository.get_candidate(candidate.id) is None:
            repository.create_candidate(candidate)
    for job in DEMO_JOBS:
        if repository.get_job(job.id) is None:
            repository.create_job(job)
    return [repository.get_candidate(item.id) for item in DEMO_CANDIDATES if repository.get_candidate(item.id)], [
        repository.get_job(item.id) for item in DEMO_JOBS if repository.get_job(item.id)
    ]

