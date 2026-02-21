# API Reference

Base URL: `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`

## Authentication

All endpoints (except `/auth/login`) require a Bearer token.

```
Authorization: Bearer <jwt_token>
```

### POST /auth/login
Form data: `username`, `password`
Response: `{ "access_token": "...", "token_type": "bearer" }`

## Datasets

### GET /datasets/
Returns list of all datasets accessible to user.

### POST /datasets/
Multipart form upload. Fields: `name`, `description` (optional), `files[]`, `file_types[]` (one per file).
Admin only.

### GET /datasets/{id}
Single dataset with parse_errors.

### DELETE /datasets/{id}
Permanently delete dataset + all events/incidents. Admin only.

## Incidents

### GET /incidents/
Query params: `dataset_id`, `status`, `severity`, `incident_type`, `limit` (default 50), `offset`.

### GET /incidents/{id}
Full incident with ai_summaries.

### POST /incidents/{id}/acknowledge
Mark as ACK. L1+.

### PATCH /incidents/{id}
Update: `status`, `severity`, `incident_type`, `assigned_to`. L2+.

### POST /incidents/{id}/close
Close incident. L2+.

### POST /incidents/{id}/summarize
Trigger LLM summarization. Returns summary object.

### GET /incidents/{id}/events
List evidence events for incident.

## Notes

### GET /notes/incidents/{incident_id}/notes
List notes for incident.

### POST /notes/incidents/{incident_id}/notes
Add note. Body: `{ "content": "...", "note_type": "TRIAGE|INVESTIGATION" }`.
L2 required for INVESTIGATION notes.

## Chat

### GET /chat/sessions
List user's chat sessions.

### POST /chat/sessions
Body: `{ "title": "...", "dataset_id": null, "incident_id": null }`.

### GET /chat/sessions/{id}/messages
List messages in session.

### POST /chat/sessions/{id}/messages
Body: `{ "content": "..." }`. Returns AI response message.

## Reports

### GET /reports/incidents/{id}/pdf
Download PDF report. L2+.

## Admin

### GET /users/
List all users. Admin only.

### POST /users/
Create user. Body: `{ "username", "password", "role", "full_name" }`. Admin only.

### PATCH /users/{id}
Update user (is_active, role, full_name). Admin only.

### GET /admin/audit-log
Query params: `action_type`, `user_id`, `limit`, `offset`. Admin only.
