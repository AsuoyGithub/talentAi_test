"""Standard-library HTTP server exposing the TalentAI JSON API."""

from __future__ import annotations

import json
import re
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from talent_ai.config import Settings, load_settings
from talent_ai.domain import Candidate, Job, MatchResult, new_id, utc_now
from talent_ai.services.matcher import MatchingEngine
from talent_ai.services.parser import ResumeParser
from talent_ai.services.report import build_match_report
from talent_ai.storage import SqliteRepository


class ApiError(Exception):
    """HTTP-facing error carrying a status code and message."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


class TalentAiHandler(BaseHTTPRequestHandler):
    """Handler for the TalentAI API and simple health endpoint."""

    server_version = "TalentAI/0.1"

    @property
    def repository(self) -> SqliteRepository:
        return self.server.repository  # type: ignore[attr-defined]

    @property
    def parser(self) -> ResumeParser:
        return self.server.parser  # type: ignore[attr-defined]

    @property
    def engine(self) -> MatchingEngine:
        return self.server.engine  # type: ignore[attr-defined]

    @property
    def settings(self) -> Settings:
        return self.server.settings  # type: ignore[attr-defined]

    def do_GET(self) -> None:  # noqa: N802 - stdlib naming
        path, query = self._parse_path()
        params = urllib.parse.parse_qs(query)
        try:
            if path == "/health":
                self._send_json({"status": "ok", "service": "talent-ai"})
            elif path == "/api/candidates":
                query_text = params.get("q", [""])[0]
                limit = self._int_query_param(params, "limit", 100, maximum=1000)
                offset = self._int_query_param(params, "offset", 0, maximum=100000)
                candidates = self.repository.list_candidates(
                    query=query_text,
                    limit=limit,
                    offset=offset,
                )
                self._send_json([candidate.to_dict() for candidate in candidates])
            elif path == "/api/jobs":
                query_text = params.get("q", [""])[0]
                limit = self._int_query_param(params, "limit", 100, maximum=1000)
                offset = self._int_query_param(params, "offset", 0, maximum=100000)
                jobs = self.repository.list_jobs(
                    query=query_text,
                    limit=limit,
                    offset=offset,
                )
                self._send_json([job.to_dict() for job in jobs])
            elif path.startswith("/api/matches/") and path.endswith("/export"):
                job_id = path.removeprefix("/api/matches/").removesuffix("/export")
                job = self._require_job(job_id)
                results = self.repository.list_match_results(job_id)
                candidates: dict[str, Candidate] = {}
                for result in results:
                    candidate = self.repository.get_candidate(result.candidate_id)
                    if candidate is not None:
                        candidates[result.candidate_id] = candidate
                report_format = params.get("format", ["csv"])[0].lower()
                try:
                    content_type, body = build_match_report(
                        job,
                        results,
                        candidates,
                        report_format=report_format,
                    )
                except ValueError as exc:
                    raise ApiError(400, str(exc)) from exc
                self._send_text(body, content_type)
            elif path.startswith("/api/matches/"):
                job_id = path.removeprefix("/api/matches/")
                self._require_job(job_id)
                results = self.repository.list_match_results(job_id)
                self._send_json([result.to_dict() for result in results])
            else:
                raise ApiError(404, "not found")
        except ApiError as exc:
            self._send_error(exc.status, exc.message)
        except Exception as exc:  # pragma: no cover - defensive boundary
            self._send_error(500, f"internal server error: {exc}")

    def do_POST(self) -> None:  # noqa: N802 - stdlib naming
        path, _ = self._parse_path()
        try:
            if path == "/api/candidates":
                payload = self._read_json()
                candidate = Candidate.from_dict({**payload, "id": new_id("candidate")})
                self.repository.create_candidate(candidate)
                self._send_json(candidate.to_dict(), status=201)
            elif path == "/api/jobs":
                payload = self._read_json()
                job = Job.from_dict({**payload, "id": new_id("job")})
                self.repository.create_job(job)
                self._send_json(job.to_dict(), status=201)
            elif path == "/api/resumes/parse":
                payload = self._read_json()
                parsed = self._parse_resume_payload(payload)
                self._send_json(parsed.to_dict())
            elif path == "/api/resumes/import":
                payload = self._read_json()
                parsed = self._parse_resume_payload(payload)
                candidate = parsed.to_candidate(resume_text=self._resume_text(payload))
                self.repository.create_candidate(candidate)
                self._send_json(candidate.to_dict(), status=201)
            elif path == "/api/matches":
                payload = self._read_json()
                results = self._match_payload(payload)
                self.repository.save_match_results(results)
                self._send_json([result.to_dict() for result in results])
            else:
                raise ApiError(404, "not found")
        except ApiError as exc:
            self._send_error(exc.status, exc.message)
        except ValueError as exc:
            self._send_error(400, str(exc))
        except Exception as exc:  # pragma: no cover - defensive boundary
            self._send_error(500, f"internal server error: {exc}")

    def do_DELETE(self) -> None:  # noqa: N802 - stdlib naming
        path, _ = self._parse_path()
        try:
            if path.startswith("/api/candidates/"):
                candidate_id = path.removeprefix("/api/candidates/")
                self._send_json({"deleted": self.repository.delete_candidate(candidate_id)})
            elif path.startswith("/api/jobs/"):
                job_id = path.removeprefix("/api/jobs/")
                self._send_json({"deleted": self.repository.delete_job(job_id)})
            else:
                raise ApiError(404, "not found")
        except ApiError as exc:
            self._send_error(exc.status, exc.message)
        except Exception as exc:  # pragma: no cover - defensive boundary
            self._send_error(500, f"internal server error: {exc}")

    def _parse_path(self) -> tuple[str, str]:
        parsed = urllib.parse.urlsplit(self.path)
        return parsed.path, parsed.query

    def _read_json(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            raise ApiError(400, "request body is required")
        if content_length > self.settings.max_upload_bytes:
            raise ApiError(413, "request body is too large")
        raw = self.rfile.read(content_length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ApiError(400, "request body must be valid JSON") from exc
        if not isinstance(payload, dict):
            raise ApiError(400, "request body must be a JSON object")
        return payload

    def _int_query_param(
        self,
        params: dict[str, list[str]],
        name: str,
        default: int,
        *,
        maximum: int,
    ) -> int:
        raw = params.get(name, [str(default)])[0]
        try:
            value = int(raw)
        except ValueError as exc:
            raise ApiError(400, f"{name} must be an integer") from exc
        if value < 0 or value > maximum:
            raise ApiError(400, f"{name} must be between 0 and {maximum}")
        return value

    def _parse_resume_payload(self, payload: dict[str, Any]) -> Any:
        text = payload.get("text")
        encoded = payload.get("base64")
        if not text and not encoded:
            raise ApiError(400, "provide text or base64")
        if encoded:
            import base64

            try:
                data = base64.b64decode(str(encoded), validate=True)
            except ValueError as exc:
                raise ApiError(400, "base64 is not valid") from exc
            return self.parser.parse_bytes(data)
        return self.parser.parse_text(str(text))

    def _resume_text(self, payload: dict[str, Any]) -> str:
        text = payload.get("text")
        if text is not None:
            return str(text)
        encoded = payload.get("base64")
        if encoded:
            import base64

            return base64.b64decode(str(encoded), validate=True).decode("utf-8")
        return ""

    def _match_payload(self, payload: dict[str, Any]) -> list[MatchResult]:
        job_id = str(payload.get("job_id", ""))
        job = self._require_job(job_id)
        candidate_ids = payload.get("candidate_ids")
        if isinstance(candidate_ids, list):
            candidates = [
                candidate
                for candidate_id in candidate_ids
                if (candidate := self.repository.get_candidate(str(candidate_id))) is not None
            ]
        elif payload.get("candidate_id"):
            candidate = self.repository.get_candidate(str(payload["candidate_id"]))
            candidates = [candidate] if candidate else []
        else:
            candidates = self.repository.list_candidates()
        if not candidates:
            return []
        return self.engine.rank(job, candidates)

    def _require_job(self, job_id: str) -> Any:
        job = self.repository.get_job(job_id)
        if job is None:
            raise ApiError(404, f"job not found: {job_id}")
        return job

    def _send_json(self, payload: Any, *, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, body: str, content_type: str, *, status: int = 200) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def _send_error(self, status: int, message: str) -> None:
        self._send_json({"error": message}, status=status)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib API
        # Keep server output concise during normal operation and tests.
        return


def create_server(
    settings: Settings | None = None, repository: SqliteRepository | None = None
) -> ThreadingHTTPServer:
    """Create a threaded HTTP server with shared services attached."""

    settings = settings or load_settings()
    owned_repository = repository is None
    repository = repository or SqliteRepository(settings.database_path)
    server = ThreadingHTTPServer((settings.host, settings.port), TalentAiHandler)
    server.settings = settings  # type: ignore[attr-defined]
    server.repository = repository  # type: ignore[attr-defined]
    server.parser = ResumeParser()  # type: ignore[attr-defined]
    server.engine = MatchingEngine()  # type: ignore[attr-defined]
    server.owned_repository = owned_repository  # type: ignore[attr-defined]
    return server


def serve(settings: Settings | None = None) -> None:
    """Run the HTTP server until interrupted."""

    settings = settings or load_settings()
    server = create_server(settings)
    host, port = server.server_address[:2]
    print(f"TalentAI listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping TalentAI")
    finally:
        server.server_close()
