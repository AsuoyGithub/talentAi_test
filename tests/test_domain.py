from __future__ import annotations

import unittest

from talent_ai.domain import Candidate, Job, normalize_skill, normalize_skills


class DomainModelTests(unittest.TestCase):
    def test_normalize_skill_strips_duplicates_and_orders(self) -> None:
        self.assertEqual(
            normalize_skills(["Python", " python ", "SQL", "python", ""]),
            ("python", "sql"),
        )

    def test_normalize_skill_is_case_insensitive(self) -> None:
        self.assertEqual(normalize_skill("FastAPI"), "fastapi")

    def test_candidate_from_dict_normalizes_fields(self) -> None:
        candidate = Candidate.from_dict(
            {
                "id": "candidate_1",
                "name": "Ada Chen",
                "email": "ADA@EXAMPLE.COM",
                "years_experience": "4.5",
                "skills": ["Python", "FastAPI"],
            }
        )
        self.assertEqual(candidate.email, "ADA@EXAMPLE.COM")
        self.assertEqual(candidate.years_experience, 4.5)
        self.assertEqual(candidate.skills, ("fastapi", "python"))

    def test_job_round_trip_preserves_skill_groups(self) -> None:
        job = Job(
            id="job_1",
            title="Backend Engineer",
            company="Acme",
            required_skills=("Python", "FastAPI"),
            preferred_skills=("Docker",),
        )
        restored = Job.from_dict(job.to_dict())
        self.assertEqual(restored.required_skills, ("fastapi", "python"))
        self.assertEqual(restored.preferred_skills, ("docker",))


if __name__ == "__main__":
    unittest.main()

