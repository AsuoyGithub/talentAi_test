from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from talent_ai.domain import Candidate, Job, MatchResult
from talent_ai.storage import SqliteRepository


class SqliteRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repository = SqliteRepository(Path(self.tempdir.name) / "talent.db")

    def tearDown(self) -> None:
        self.repository.close()
        self.tempdir.cleanup()

    def test_candidate_and_job_crud(self) -> None:
        candidate = Candidate(
            id="candidate_1",
            name="Ada Chen",
            email="ada@example.com",
            skills=("python", "fastapi"),
            years_experience=5,
        )
        job = Job(
            id="job_1",
            title="Backend Engineer",
            company="Acme",
            required_skills=("python", "fastapi"),
        )

        self.repository.create_candidate(candidate)
        self.repository.create_job(job)

        self.assertEqual(self.repository.get_candidate("candidate_1"), candidate)
        self.assertEqual(self.repository.get_job("job_1"), job)
        self.assertEqual(len(self.repository.list_candidates(query="ada")), 1)
        self.assertEqual(len(self.repository.list_jobs(query="backend")), 1)

    def test_duplicate_candidate_email_is_rejected(self) -> None:
        first = Candidate(id="candidate_1", name="Ada", email="ada@example.com")
        second = Candidate(id="candidate_2", name="Other Ada", email="ada@example.com")
        self.repository.create_candidate(first)
        with self.assertRaises(ValueError):
            self.repository.create_candidate(second)

    def test_match_results_are_replaced_and_sorted(self) -> None:
        job = Job(id="job_1", title="Engineer", company="Acme")
        candidate = Candidate(id="candidate_1", name="Ada", email="ada@example.com")
        self.repository.create_job(job)
        self.repository.create_candidate(candidate)

        first = MatchResult(
            job_id="job_1",
            candidate_id="candidate_1",
            score=75.0,
            reasons=("Matched required skills",),
        )
        self.repository.save_match_results([first])
        self.assertEqual(self.repository.list_match_results("job_1"), [first])

    def test_delete_cascade_removes_match_results(self) -> None:
        job = Job(id="job_1", title="Engineer", company="Acme")
        candidate = Candidate(id="candidate_1", name="Ada", email="ada@example.com")
        self.repository.create_job(job)
        self.repository.create_candidate(candidate)
        self.repository.save_match_results(
            [MatchResult(job_id="job_1", candidate_id="candidate_1", score=80.0)]
        )

        self.repository.delete_candidate("candidate_1")
        self.assertEqual(self.repository.list_match_results("job_1"), [])


if __name__ == "__main__":
    unittest.main()

