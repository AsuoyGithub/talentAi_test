"""Deterministic candidate-to-job matching and scoring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from talent_ai.domain import Candidate, Job, MatchResult


@dataclass(frozen=True)
class MatchingWeights:
    """Weights used to combine the three score components."""

    required_skills: float = 60.0
    preferred_skills: float = 20.0
    experience: float = 20.0

    def __post_init__(self) -> None:
        weights = (self.required_skills, self.preferred_skills, self.experience)
        if any(weight < 0 for weight in weights):
            raise ValueError("matching weights cannot be negative")
        if sum(weights) != 100.0:
            raise ValueError("matching weights must add up to 100")


class MatchingEngine:
    """Score candidates against a job using transparent, testable rules."""

    def __init__(self, weights: MatchingWeights | None = None) -> None:
        self.weights = weights or MatchingWeights()

    def match(self, job: Job, candidate: Candidate) -> MatchResult:
        required = set(job.required_skills)
        preferred = set(job.preferred_skills)
        candidate_skills = set(candidate.skills)

        matched_required = sorted(required & candidate_skills)
        missing_required = sorted(required - candidate_skills)
        matched_preferred = sorted(preferred & candidate_skills)

        required_score = self._ratio(len(matched_required), len(required)) * self.weights.required_skills
        preferred_score = self._ratio(len(matched_preferred), len(preferred)) * self.weights.preferred_skills
        experience_score = self._experience_score(job.min_years_experience, candidate.years_experience)

        score = round(
            max(0.0, min(100.0, required_score + preferred_score + experience_score)),
            2,
        )
        reasons = self._reasons(
            job=job,
            candidate=candidate,
            matched_required=matched_required,
            missing_required=missing_required,
            matched_preferred=matched_preferred,
            experience_score=experience_score,
        )
        return MatchResult(
            job_id=job.id,
            candidate_id=candidate.id,
            score=score,
            matched_required=tuple(matched_required),
            missing_required=tuple(missing_required),
            matched_preferred=tuple(matched_preferred),
            reasons=tuple(reasons),
        )

    def rank(self, job: Job, candidates: Iterable[Candidate]) -> list[MatchResult]:
        results = [self.match(job, candidate) for candidate in candidates]
        return sorted(results, key=lambda result: result.score, reverse=True)

    def match_all(
        self, jobs: Iterable[Job], candidates: Iterable[Candidate]
    ) -> dict[str, list[MatchResult]]:
        return {
            job.id: self.rank(job, candidates)
            for job in jobs
        }

    def _experience_score(self, required_years: float, actual_years: float) -> float:
        if required_years <= 0:
            return self.weights.experience
        if actual_years <= 0:
            return 0.0
        return min(actual_years / required_years, 1.0) * self.weights.experience

    @staticmethod
    def _ratio(actual: int, expected: int) -> float:
        if expected == 0:
            return 1.0
        return actual / expected

    def _reasons(
        self,
        *,
        job: Job,
        candidate: Candidate,
        matched_required: list[str],
        missing_required: list[str],
        matched_preferred: list[str],
        experience_score: float,
    ) -> list[str]:
        reasons = [
            f"matched {len(matched_required)}/{len(job.required_skills)} required skills"
        ]
        if missing_required:
            reasons.append("missing required skills: " + ", ".join(missing_required))
        if job.preferred_skills:
            reasons.append(
                f"matched {len(matched_preferred)}/{len(job.preferred_skills)} preferred skills"
            )
        if job.min_years_experience > 0:
            reasons.append(
                f"experience score {experience_score:.2f} "
                f"(candidate {candidate.years_experience:.1f} years, "
                f"required {job.min_years_experience:.1f} years)"
            )
        else:
            reasons.append("no minimum experience requirement")
        return reasons

