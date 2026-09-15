# Product Requirements

## Purpose

TalentAI is a small recruitment tool that stores candidates and open jobs,
parses plain-text resumes, and ranks candidates against a job by comparing
required skills, preferred skills, and experience.

The matching logic is intentionally deterministic so results can be
reproduced and tested without external AI providers.

## Users

- **Recruiter** creates jobs, adds candidates, and reviews ranked matches.
- **Administrator** initializes storage, seeds demo data, and operates the API.

## Functional Requirements

### FR-1 Candidate Management

A candidate has a stable string ID, name, email, phone, location, years of
experience, normalized skills, education, optional resume text, and a creation
timestamp.

The repository enforces unique email addresses and normalizes skill labels
for consistent comparison. Candidates can be listed, created, and deleted
through the API or CLI.

### FR-2 Job Management

A job has a stable string ID, title, company, location, description, minimum
years of experience, required skills, preferred skills, and a creation
timestamp.

Required and preferred skills are normalized before matching. Jobs can be
listed, created, and deleted.

### FR-3 Resume Parsing

The parser accepts UTF-8 plain text directly or as base64-encoded bytes.

It extracts:

- name from the first non-contact header line
- email and phone with regular expressions
- a known location
- explicit years of experience or a year range
- skills from a curated keyword list
- the first education marker line

Empty input, missing files, and invalid UTF-8 input raise `ResumeParseError`.

### FR-4 Matching

The engine compares a candidate with a job and returns:

- a score from 0 to 100
- required skills that matched
- required skills that are missing
- preferred skills that matched
- human-readable reasons for the score

Default weights are 60% required skills, 20% preferred skills, and 20%
experience. The weights must always sum to 100.

### FR-5 HTTP API

The API exposes health, candidate, job, resume parsing, resume import, and
match endpoints. All responses are JSON, including errors.

The threaded HTTP server shares a SQLite repository and parses or matches each
request on the worker thread.

### FR-6 Persistence

Data is stored in SQLite with foreign keys enabled. Schema creation is
idempotent and owned by `SqliteRepository`.

Deleting a candidate or job also removes its stored match results through
foreign-key cascades.

## Non-functional Requirements

- Run with Python 3.11 or newer.
- Use only the Python standard library at runtime.
- Provide automated unit and integration tests.
- Keep the API stateless except for SQLite persistence.
- Avoid secrets in committed files.
- Keep deterministic behavior reproducible across runs.

## Non-goals

- Authentication and multi-tenant isolation.
- OCR, PDF parsing, or binary attachment extraction.
- A user-facing web interface.
- A vector database or learned ranking model.
- Background job processing or distributed queues.

## Acceptance Criteria

1. `python -m unittest discover -v` passes from the repository root.
2. `python -m compileall -q src` completes without syntax errors.
3. The HTTP server starts and `GET /health` returns a healthy response.
4. Seeded data can be matched and produces reproducible scores.
5. A fresh SQLite database is created automatically.
6. The README accurately reflects the implemented commands and endpoints.
