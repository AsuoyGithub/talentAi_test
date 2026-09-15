from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from talent_ai.seed import seed_demo_data
from talent_ai.storage import SqliteRepository


class SeedTests(unittest.TestCase):
    def test_seed_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            with SqliteRepository(Path(tempdir) / "talent.db") as repository:
                first_candidates, first_jobs = seed_demo_data(repository)
                second_candidates, second_jobs = seed_demo_data(repository)
                self.assertEqual(len(first_candidates), len(second_candidates))
                self.assertEqual(len(first_jobs), len(second_jobs))
                self.assertEqual(len(repository.list_candidates()), 3)
                self.assertEqual(len(repository.list_jobs()), 2)


if __name__ == "__main__":
    unittest.main()
