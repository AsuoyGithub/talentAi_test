from __future__ import annotations

import unittest

from talent_ai.domain import Candidate, Job
from talent_ai.services.matcher import MatchingEngine, MatchingWeights


class MatchingEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = MatchingEngine()
        self.job = Job(
            id="job_1",
            title="Backend Engineer",
            company="Acme",
            min_years_experience=4,
            required_skills=("python", "fastapi", "postgresql"),
            preferred_skills=("docker", "aws"),
        )

    def test_full_match_gets_perfect_score(self) -> None:
        candidate = Candidate(
            id="candidate_1",
            name="Ada",
            email="ada@example.com",
            years_experience=5,
            skills=("python", "fastapi", "postgresql", "docker", "aws"),
        )
        result = self.engine.match(self.job, candidate)
        self.assertEqual(result.score, 100.0)
        self.assertEqual(result.missing_required, ())

    def test_missing_required_skills_reduce_score(self) -> None:
        candidate = Candidate(
            id="candidate_1",
            name="Ada",
            email="ada@example.com",
            years_experience=2,
            skills=("python",),
        )
        result = self.engine.match(self.job, candidate)
        self.assertEqual(result.missing_required, ("fastapi", "postgresql"))
        self.assertLess(result.score, 100.0)
        self.assertGreater(result.score, 0.0)

    def test_experience_below_requirement_caps_component(self) -> None:
        candidate = Candidate(
            id="candidate_1",
            name="Ada",
            email="ada@example.com",
            years_experience=2,
            skills=("python", "fastapi", "postgresql"),
        )
        result = self.engine.match(self.job, candidate)
        self.assertLess(result.score, 100.0)
        self.assertAlmostEqual(result.score, 70.0, places=2)

    def test_rank_sorts_highest_first(self) -> None:
        strong = Candidate(
            id="strong",
            name="Strong",
            email="strong@example.com",
            years_experience=6,
            skills=("python", "fastapi", "postgresql", "docker", "aws"),
        )
        weak = Candidate(
            id="weak",
            name="Weak",
            email="weak@example.com",
            years_experience=1,
            skills=("python",),
        )
        ranked = self.engine.rank(self.job, [weak, strong])
        self.assertEqual(ranked[0].candidate_id, "strong")
        self.assertEqual(ranked[-1].candidate_id, "weak")

    def test_weights_must_sum_to_one_hundred(self) -> None:
        with self.assertRaises(ValueError):
            MatchingWeights(required_skills=50, preferred_skills=20, experience=20)


if __name__ == "__main__":
    unittest.main()

