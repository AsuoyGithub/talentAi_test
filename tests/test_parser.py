from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from talent_ai.services.parser import ResumeParser, ResumeParseError


SAMPLE_RESUME = """\
Ada Chen
ada.chen@example.com
+86 138 0000 0001
Shanghai

Backend engineer with 6 years of experience building Python and FastAPI services.
Skills: Python, FastAPI, PostgreSQL, Docker, AWS

Master of Software Engineering
"""


class ResumeParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = ResumeParser()

    def test_parse_text_extracts_expected_fields(self) -> None:
        parsed = self.parser.parse_text(SAMPLE_RESUME)
        self.assertEqual(parsed.name, "Ada Chen")
        self.assertEqual(parsed.email, "ada.chen@example.com")
        self.assertEqual(parsed.location, "shanghai")
        self.assertEqual(parsed.years_experience, 6.0)
        self.assertIn("python", parsed.skills)
        self.assertIn("fastapi", parsed.skills)
        self.assertIn("docker", parsed.skills)
        self.assertIn("Master of Software Engineering", parsed.education)

    def test_parse_empty_text_fails(self) -> None:
        with self.assertRaises(ResumeParseError):
            self.parser.parse_text("  ")

    def test_parse_file_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "resume.txt"
            path.write_text(SAMPLE_RESUME, encoding="utf-8")
            parsed = self.parser.parse_file(path)
        self.assertEqual(parsed.name, "Ada Chen")

    def test_parse_file_missing_path_fails(self) -> None:
        with self.assertRaises(ResumeParseError):
            self.parser.parse_file("missing-resume.txt")

    def test_parse_bytes_handles_invalid_utf8(self) -> None:
        with self.assertRaises(ResumeParseError):
            self.parser.parse_bytes(b"\xff\xfe\x00bad")

    def test_to_candidate_preserves_resume_text(self) -> None:
        candidate = self.parser.parse_text(SAMPLE_RESUME).to_candidate(
            resume_text=SAMPLE_RESUME
        )
        self.assertTrue(candidate.id.startswith("candidate_"))
        self.assertEqual(candidate.resume_text, SAMPLE_RESUME.strip())


if __name__ == "__main__":
    unittest.main()

