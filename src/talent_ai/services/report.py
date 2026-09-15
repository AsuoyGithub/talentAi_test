"""Report builders for match results."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable, Mapping

from talent_ai.domain import Candidate, Job, MatchResult


CSV_HEADER = (
    "job_id",
    "job_title",
    "candidate_id",
    "candidate_name",
    "score",
    "matched_required",
    "missing_required",
    "matched_preferred",
    "reasons",
)


def _row(result: MatchResult, job: Job, candidate: Candidate | None) -> dict[str, object]:
    return {
        "job_id": job.id,
        "job_title": job.title,
        "candidate_id": result.candidate_id,
        "candidate_name": candidate.name if candidate else "",
        "score": result.score,
        "matched_required": ",".join(result.matched_required),
        "missing_required": ",".join(result.missing_required),
        "matched_preferred": ",".join(result.matched_preferred),
        "reasons": "; ".join(result.reasons),
    }


def build_match_report(
    job: Job,
    results: Iterable[MatchResult],
    candidates: Mapping[str, Candidate],
    *,
    report_format: str = "csv",
) -> tuple[str, str]:
    """Return a content type and serialized report body."""

    ordered = sorted(results, key=lambda result: result.score, reverse=True)
    rows = [_row(result, job, candidates.get(result.candidate_id)) for result in ordered]

    if report_format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=CSV_HEADER)
        writer.writeheader()
        writer.writerows(rows)
        return "text/csv; charset=utf-8", output.getvalue()

    if report_format == "json":
        return "application/json; charset=utf-8", json.dumps(rows, indent=2)

    raise ValueError(f"unsupported report format: {report_format}")
