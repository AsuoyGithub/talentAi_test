from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from talent_ai.cli import main
from talent_ai.domain import Candidate, Job, MatchResult
from talent_ai.services.report import build_match_report
from talent_ai.storage import SqliteRepository


class MatchReportTests(unittest.TestCase):
    def test_csv_report_contains_ranked_candidate_rows(self) -> None:
        job = Job(id="job_1", title="Backend Engineer", company="Acme")
        candidate = Candidate(id="candidate_1", name="Ada", email="ada@example.com")
        result = MatchResult(
            job_id="job_1",
            candidate_id="candidate_1",
            score=88.5,
            matched_required=("python",),
            reasons=("matched 1/1 required skills",),
        )

        content_type, body = build_match_report(
            job,
            [result],
            {"candidate_1": candidate},
            report_format="csv",
        )

        self.assertIn("text/csv", content_type)
        self.assertIn("job_id,job_title", body)
        self.assertIn("Ada", body)
        self.assertIn("88.5", body)

    def test_json_report_is_deserializable(self) -> None:
        job = Job(id="job_1", title="Backend Engineer", company="Acme")
        candidate = Candidate(id="candidate_1", name="Ada", email="ada@example.com")
        result = MatchResult(
            job_id="job_1",
            candidate_id="candidate_1",
            score=72.0,
        )

        _, body = build_match_report(
            job,
            [result],
            {"candidate_1": candidate},
            report_format="json",
        )

        rows = json.loads(body)
        self.assertEqual(rows[0]["candidate_name"], "Ada")


class CliExportTests(unittest.TestCase):
    def test_export_matches_command_prints_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            database_path = Path(tempdir) / "talent.db"
            with SqliteRepository(database_path) as repository:
                repository.create_job(
                    Job(
                        id="job_1",
                        title="Backend Engineer",
                        company="Acme",
                        required_skills=("python",),
                    )
                )
                repository.create_candidate(
                    Candidate(
                        id="candidate_1",
                        name="Ada",
                        email="ada@example.com",
                        skills=("python",),
                    )
                )
                repository.save_match_results(
                    [
                        MatchResult(
                            job_id="job_1",
                            candidate_id="candidate_1",
                            score=95.0,
                        )
                    ]
                )

            output = io.StringIO()
            with patch.dict(os.environ, {"TALENT_AI_DB": str(database_path)}):
                with redirect_stdout(output):
                    self.assertEqual(
                        main(["export-matches", "job_1", "--format", "csv"]),
                        0,
                    )

            self.assertIn("candidate_name", output.getvalue())
            self.assertIn("Ada", output.getvalue())


if __name__ == "__main__":
    unittest.main()
