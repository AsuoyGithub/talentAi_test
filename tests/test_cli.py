"""Tests for CLI behavior."""

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
from talent_ai.storage import SqliteRepository


class CliTests(unittest.TestCase):
    def test_seed_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "cli.db"
            with patch.dict(os.environ, {"TALENT_AI_DB": str(database_path)}, clear=False):
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(["seed"]), 0)
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(["seed"]), 0)

            with SqliteRepository(database_path) as repository:
                self.assertEqual(len(repository.list_candidates()), 3)
                self.assertEqual(len(repository.list_jobs()), 2)

    def test_parse_command_prints_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "resume.txt"
            path.write_text(
                "Alice\n"
                "alice@example.com\n"
                "+86 138 0000 1111\n"
                "Shanghai\n"
                "3 years with Python and SQL.",
                encoding="utf-8",
            )
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["parse", str(path)]), 0)
            payload = json.loads(output.getvalue())
            self.assertEqual(payload["email"], "alice@example.com")
            self.assertEqual(payload["years_experience"], 3.0)


if __name__ == "__main__":
    unittest.main()
