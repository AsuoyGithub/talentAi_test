from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from talent_ai.api.server import create_server
from talent_ai.config import Settings


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tempdir = tempfile.TemporaryDirectory()
        settings = Settings(
            database_path=Path(cls.tempdir.name) / "talent.db",
            host="127.0.0.1",
            port=0,
            max_upload_bytes=100_000,
        )
        cls.server = create_server(settings)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.server.repository.close()  # type: ignore[attr-defined]
        cls.tempdir.cleanup()

    def request(self, method: str, path: str, payload: dict | None = None):
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def test_health_check(self) -> None:
        status, payload = self.request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "ok")

    def test_candidate_and_job_creation(self) -> None:
        status, candidate = self.request(
            "POST",
            "/api/candidates",
            {
                "name": "Ada Chen",
                "email": "ada.api@example.com",
                "location": "shanghai",
                "years_experience": 5,
                "skills": ["python", "fastapi", "docker"],
            },
        )
        self.assertEqual(status, 201)

        status, job = self.request(
            "POST",
            "/api/jobs",
            {
                "title": "Backend Engineer",
                "company": "Acme",
                "min_years_experience": 4,
                "required_skills": ["python", "fastapi"],
                "preferred_skills": ["docker"],
            },
        )
        self.assertEqual(status, 201)

        status, matches = self.request(
            "POST",
            "/api/matches",
            {"job_id": job["id"]},
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["candidate_id"], candidate["id"])

    def test_parse_and_import_resume(self) -> None:
        resume_text = (
            "Ada Chen\nada.resume@example.com\nShanghai\n"
            "6 years of experience with Python, FastAPI, Docker"
        )
        status, parsed = self.request(
            "POST", "/api/resumes/parse", {"text": resume_text}
        )
        self.assertEqual(status, 200)
        self.assertEqual(parsed["email"], "ada.resume@example.com")
        self.assertIn("python", parsed["skills"])

        status, candidate = self.request(
            "POST", "/api/resumes/import", {"text": resume_text}
        )
        self.assertEqual(status, 201)
        self.assertEqual(candidate["email"], "ada.resume@example.com")

    def test_candidate_list_pagination_and_delete(self) -> None:
        first = self.request(
            "POST",
            "/api/candidates",
            {
                "name": "Page One",
                "email": "page.one@example.com",
                "skills": ["python"],
            },
        )
        second = self.request(
            "POST",
            "/api/candidates",
            {
                "name": "Page Two",
                "email": "page.two@example.com",
                "skills": ["sql"],
            },
        )
        self.assertEqual(first[0], 201)
        self.assertEqual(second[0], 201)

        status, page = self.request(
            "GET",
            "/api/candidates?limit=1&offset=0",
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(page), 1)

        status, deleted = self.request(
            "DELETE",
            f"/api/candidates/{first[1]['id']}",
        )
        self.assertEqual(status, 200)
        self.assertTrue(deleted["deleted"])

    def test_match_export_endpoint_returns_csv(self) -> None:
        _, candidate = self.request(
            "POST",
            "/api/candidates",
            {
                "name": "Export Candidate",
                "email": "export.candidate@example.com",
                "skills": ["python"],
            },
        )
        _, job = self.request(
            "POST",
            "/api/jobs",
            {
                "title": "Export Job",
                "company": "Acme",
                "required_skills": ["python"],
            },
        )
        self.request("POST", "/api/matches", {"job_id": job["id"]})

        request = urllib.request.Request(
            self.base_url + f"/api/matches/{job['id']}/export?format=csv"
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8")
            content_type = response.headers["Content-Type"]

        self.assertIn("text/csv", content_type)
        self.assertIn("candidate_name", body)
        self.assertIn(candidate["name"], body)

    def test_invalid_json_is_rejected(self) -> None:
        request = urllib.request.Request(
            self.base_url + "/api/candidates",
            data=b"{not-json",
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(urllib.error.HTTPError) as context:
            urllib.request.urlopen(request, timeout=5)
        self.assertEqual(context.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
