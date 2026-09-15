# HTTP API

The API listens on `127.0.0.1:8080` by default and returns JSON for every
route. Requests use the `application/json` content type unless stated
otherwise.

## Health

### `GET /health`

```json
{
  "status": "ok",
  "service": "talent-ai"
}
```

## Candidates

### `GET /api/candidates`

Optional query parameters are `q`, `limit`, and `offset`. `q` searches name,
email, and location. The response is an array:

```json
[
  {
    "id": "candidate_demo_1",
    "name": "Ada Chen",
    "email": "ada.chen@example.com",
    "phone": "+86 138 0000 0001",
    "location": "shanghai",
    "years_experience": 6.0,
    "skills": ["aws", "docker", "fastapi", "postgresql", "python"],
    "education": "Master of Software Engineering",
    "resume_text": "Backend engineer with six years of experience...",
    "created_at": "2026-09-15T12:00:00+00:00"
  }
]
```

### `POST /api/candidates`

Request:

```json
{
  "name": "Ada Chen",
  "email": "ada@example.com",
  "phone": "+86 138 0000 1111",
  "location": "shanghai",
  "years_experience": 5,
  "skills": ["python", "fastapi"],
  "education": "Master of Software Engineering",
  "resume_text": "Optional full resume text."
}
```

The response is `201 Created` with the stored candidate. Skill labels are
normalized and sorted.

### `DELETE /api/candidates/{id}`

Deletes a candidate and its stored match results. Returns:

```json
{
  "deleted": true
}
```

## Jobs

### `GET /api/jobs`

Optional query parameters are `q`, `limit`, and `offset`. `q` searches title,
company, and location. The response is an array of job objects.

### `POST /api/jobs`

Request:

```json
{
  "title": "Backend Engineer",
  "company": "Acme AI",
  "location": "shanghai",
  "description": "Build scalable Python services.",
  "min_years_experience": 4,
  "required_skills": ["python", "fastapi", "postgresql"],
  "preferred_skills": ["docker", "aws"]
}
```

The response is `201 Created` with the stored job.

### `DELETE /api/jobs/{id}`

Deletes a job and its stored match results.

## Resume Parsing

### `POST /api/resumes/parse`

Provide either `text` or `base64`.

```json
{
  "text": "Ada Chen\nada@example.com\nShanghai\n6 years of experience with Python and FastAPI."
}
```

Response:

```json
{
  "name": "Ada Chen",
  "email": "ada@example.com",
  "phone": "",
  "location": "shanghai",
  "years_experience": 6.0,
  "skills": ["fastapi", "python"],
  "education": ""
}
```

### `POST /api/resumes/import`

Uses the same `text` or `base64` input, but persists a candidate instead of
only returning parsed fields. The response is `201 Created`.

## Matches

### `POST /api/matches`

By default, this ranks every stored candidate against one job, persists each
result, and returns the ordered list.

```json
{
  "job_id": "job_demo_1"
}
```

Optionally restrict candidates with `candidate_id` or `candidate_ids`:

```json
{
  "job_id": "job_demo_1",
  "candidate_ids": ["candidate_demo_1", "candidate_demo_2"]
}
```

Response:

```json
[
  {
    "job_id": "job_demo_1",
    "candidate_id": "candidate_demo_1",
    "score": 100.0,
    "matched_required": ["fastapi", "postgresql", "python"],
    "missing_required": [],
    "matched_preferred": ["aws", "docker"],
    "reasons": [
      "matched 3/3 required skills",
      "matched 2/2 preferred skills",
      "experience score 20.00 (candidate 6.0 years, required 4.0 years)"
    ],
    "created_at": "2026-09-15T12:00:00+00:00"
  }
]
```

### `GET /api/matches/{job_id}`

Returns previously saved match results for a job, sorted by descending score.

### `GET /api/matches/{job_id}/export`

Returns a serialized report for the saved match results. The default format is
CSV; use `?format=json` for JSON output.

```text
GET /api/matches/job_demo_1/export?format=csv
```

The CSV response includes job title, candidate name, score, matched and
missing skills, and human-readable reasons.

## Errors

Errors use a consistent JSON shape:

```json
{
  "error": "job not found: job_missing"
}
```

Common status codes are `400` for invalid input, `404` for missing routes or
resources, `413` for oversized request bodies, and `500` for unexpected
failures.
