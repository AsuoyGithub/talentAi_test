"""Command-line interface for local setup and evaluation."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from talent_ai.config import load_settings
from talent_ai.domain import Candidate, Job, new_id
from talent_ai.seed import seed_demo_data
from talent_ai.services.matcher import MatchingEngine
from talent_ai.services.parser import ResumeParser
from talent_ai.storage import SqliteRepository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="talent-ai",
        description="Local command line interface for TalentAI.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="create the SQLite schema")
    subparsers.add_parser("seed", help="insert idempotent demo data")
    subparsers.add_parser("serve", help="start the HTTP server")
    subparsers.add_parser("list-candidates", help="list stored candidates")
    subparsers.add_parser("list-jobs", help="list stored jobs")

    parse_parser = subparsers.add_parser("parse", help="parse a resume file")
    parse_parser.add_argument("file")

    match_parser = subparsers.add_parser("match", help="rank candidates for a job")
    match_parser.add_argument("job_id")

    candidate_parser = subparsers.add_parser("add-candidate", help="create a candidate")
    candidate_parser.add_argument("--name", required=True)
    candidate_parser.add_argument("--email", required=True)
    candidate_parser.add_argument("--phone", default="")
    candidate_parser.add_argument("--location", default="")
    candidate_parser.add_argument("--experience", type=float, default=0.0)
    candidate_parser.add_argument("--skills", default="")
    candidate_parser.add_argument("--education", default="")

    job_parser = subparsers.add_parser("add-job", help="create a job")
    job_parser.add_argument("--title", required=True)
    job_parser.add_argument("--company", required=True)
    job_parser.add_argument("--location", default="")
    job_parser.add_argument("--description", default="")
    job_parser.add_argument("--experience", type=float, default=0.0)
    job_parser.add_argument("--required-skills", default="")
    job_parser.add_argument("--preferred-skills", default="")
    return parser


def _split_skills(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = load_settings()

    if args.command == "init-db":
        with SqliteRepository(settings.database_path) as repository:
            repository.initialize()
        print(f"initialized {settings.database_path}")
        return 0

    if args.command == "seed":
        with SqliteRepository(settings.database_path) as repository:
            candidates, jobs = seed_demo_data(repository)
        print(f"seeded {len(candidates)} candidates and {len(jobs)} jobs")
        return 0

    if args.command == "serve":
        from talent_ai.api.server import serve

        serve(settings)
        return 0

    if args.command == "parse":
        parsed = ResumeParser().parse_file(args.file)
        print(json.dumps(parsed.to_dict(), indent=2, ensure_ascii=False))
        return 0

    with SqliteRepository(settings.database_path) as repository:
        if args.command == "list-candidates":
            for candidate in repository.list_candidates():
                print(f"{candidate.id}\t{candidate.name}\t{candidate.email}")
            return 0
        if args.command == "list-jobs":
            for job in repository.list_jobs():
                print(f"{job.id}\t{job.title}\t{job.company}")
            return 0
        if args.command == "match":
            job = repository.get_job(args.job_id)
            if job is None:
                print(f"job not found: {args.job_id}")
                return 1
            results = MatchingEngine().rank(job, repository.list_candidates())
            repository.save_match_results(results)
            for result in results:
                candidate = repository.get_candidate(result.candidate_id)
                name = candidate.name if candidate else result.candidate_id
                print(f"{result.score:>6.2f}\t{name}")
            return 0
        if args.command == "add-candidate":
            candidate = Candidate(
                id=new_id("candidate"),
                name=args.name,
                email=args.email,
                phone=args.phone,
                location=args.location,
                years_experience=args.experience,
                skills=_split_skills(args.skills),
                education=args.education,
            )
            repository.create_candidate(candidate)
            print(candidate.id)
            return 0
        if args.command == "add-job":
            job = Job(
                id=new_id("job"),
                title=args.title,
                company=args.company,
                location=args.location,
                description=args.description,
                min_years_experience=args.experience,
                required_skills=_split_skills(args.required_skills),
                preferred_skills=_split_skills(args.preferred_skills),
            )
            repository.create_job(job)
            print(job.id)
            return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

