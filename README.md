# TalentAI

TalentAI is a small recruitment service that stores candidates and open jobs,
parses plain-text resumes, and produces deterministic, explainable match
scores. It uses only the Python standard library at runtime, which keeps the
project simple to run, test, and audit.

## Features

- Candidate and job management through a JSON HTTP API or local CLI.
- Plain-text resume parsing for name, contact details, location, experience,
  education, and skills.
- Deterministic matching based on required skills, preferred skills, and
  years of experience.
- Persistent SQLite storage with foreign-key constraints and idempotent
  schema creation.
- Reproducible demo data and an automated unit/integration test suite.
- Container-friendly deployment with a Dockerfile and Docker Compose setup.

## Architecture

The application is split into delivery, service, persistence, and domain
layers. See [docs/architecture.md](docs/architecture.md) for module details.

```text
CLI / HTTP API
      |
      v
Resume parser / matching engine
      |
      v
SQLite repository
      |
      v
Candidate, Job, and MatchResult domain models
```

## Quick Start

Python 3.11 or newer is required. The project has no runtime packages outside
the standard library.

```bash
python -m pip install -e .
python -m talent_ai init-db
python -m talent_ai seed
python -m talent_ai serve
```

If you do not want to install the package, set `PYTHONPATH` to the source
directory:

```bash
PYTHONPATH=src python -m talent_ai init-db
PYTHONPATH=src python -m talent_ai seed
PYTHONPATH=src python -m talent_ai serve
```

On Windows PowerShell, use:

```powershell
$env:PYTHONPATH = "src"
python -m talent_ai init-db
python -m talent_ai seed
python -m talent_ai serve
```

The HTTP service listens on `http://127.0.0.1:8080` by default.

## Command Line Interface

```text
python -m talent_ai init-db
python -m talent_ai seed
python -m talent_ai serve
python -m talent_ai parse resume.txt
python -m talent_ai list-candidates
python -m talent_ai list-jobs
python -m talent_ai match job_demo_1
python -m talent_ai export-matches job_demo_1 --format csv
```

Use `python -m talent_ai --help` for the full command list.

## HTTP API

The API returns JSON. A complete reference is available in
[docs/api.md](docs/api.md).

Create a candidate:

```bash
curl -X POST http://127.0.0.1:8080/api/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ada Chen",
    "email": "ada@example.com",
    "location": "shanghai",
    "years_experience": 6,
    "skills": ["python", "fastapi", "postgresql"]
  }'
```

Rank all stored candidates for a job:

```bash
curl -X POST http://127.0.0.1:8080/api/matches \
  -H "Content-Type: application/json" \
  -d '{"job_id": "job_demo_1"}'
```

## Configuration

Settings are loaded from environment variables.

| Variable | Default | Purpose |
| --- | --- | --- |
| `TALENT_AI_DB` | `~/.talent-ai/talent.db` | SQLite database path |
| `TALENT_AI_HOST` | `127.0.0.1` | HTTP bind host |
| `TALENT_AI_PORT` | `8080` | HTTP bind port |
| `TALENT_AI_MAX_UPLOAD_BYTES` | `1000000` | Maximum JSON request body size |
| `TALENT_AI_HOME` | `~/.talent-ai` | Default data directory |

See [.env.example](.env.example) for a local environment template.

## Tests

Run the complete suite from the repository root:

```bash
python -m unittest discover -v
```

The tests cover domain normalization, resume parsing, deterministic matching,
SQLite persistence, CLI commands, and HTTP integration flows.

## Docker

```bash
docker compose up --build
```

The container stores the SQLite database in the `./data` directory through the
mounted volume defined in `docker-compose.yml`.

## Project Layout

```text
src/talent_ai/
  api/server.py       HTTP routing and JSON responses
  services/parser.py  Resume text extraction
  services/matcher.py Match scoring and ranking
  services/report.py  CSV and JSON match reports
  domain.py           Candidate, Job, and MatchResult models
  storage.py          SQLite repository and schema
  config.py           Environment-backed settings
  cli.py              Operator command line
  seed.py             Reproducible demo data
tests/                Automated unit and integration tests
docs/                 Architecture, requirements, and API reference
migrations/           Reference SQL schema
```

## Documentation

- [Product requirements](docs/requirements.md)
- [Architecture](docs/architecture.md)
- [HTTP API](docs/api.md)
- [Milestone plan](docs/milestones.md)

## Current Limitations

- Resume parsing is plain-text only; PDF, DOCX, and OCR are not implemented.
- The matching engine uses transparent rules rather than a learned model.
- Authentication, authorization, and multi-tenant isolation are out of scope.

## License

MIT. See [LICENSE](LICENSE).
