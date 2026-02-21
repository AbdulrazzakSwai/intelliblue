# Data Model

All primary keys are UUIDs (String(36) for cross-DB compatibility). All timestamps are UTC.

## users
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| username | String unique | |
| password_hash | String | bcrypt |
| role | Enum(L1/L2/ADMIN) | |
| full_name | String | |
| is_active | Boolean | |
| created_at | DateTime | |
| last_login | DateTime | |

## datasets
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| name | String | |
| description | Text | |
| status | Enum | UPLOADING/PARSING/CORRELATING/SUMMARIZING/READY/ERROR |
| uploaded_by | FK users | |
| uploaded_at | DateTime | |
| event_count | Integer | |
| incident_count | Integer | |
| parse_errors | JSON | Array of {file, error} |

## events
Key fields: id, dataset_id, raw_file_id, event_time (indexed), source_type, host, username (indexed), src_ip (indexed), dst_ip, src_port, dst_port, event_type, severity_hint, http_method, url_path, http_status, user_agent, response_size, signature_id, signature, category, ids_priority, protocol, message, raw_json (JSON), extras (JSON)

Composite indexes: (dataset_id, event_time), (src_ip, event_time)

## incidents
Key fields: id, dataset_id, title, status (NEW/ACK/INVESTIGATING/CLOSED), severity (LOW/MEDIUM/HIGH/CRITICAL), incident_type, confidence (0-100), rule_id, rule_explanation, created_at, updated_at, acknowledged_by, acknowledged_at, assigned_to, closed_by, closed_at

Index: (dataset_id, status)

## incident_events
Links incidents to their evidence events. Fields: id, incident_id, event_id, relevance (primary/corroborating/context). Unique constraint: (incident_id, event_id).

## incident_notes
Fields: id, incident_id, note_type (TRIAGE/INVESTIGATION), content, author_id, created_at, updated_at.

## incident_ai_summaries
Fields: id, incident_id, summary_json (JSON), narrative, model_name, prompt_version, generation_time_sec, created_at.

summary_json structure:
```json
{
  "summary": "...",
  "what_happened": "...",
  "why_it_matters": "...",
  "likely_technique": "...",
  "recommended_next_steps": "...",
  "what_to_check_next": "...",
  "confidence_reasoning": "..."
}
```

## chat_sessions / chat_messages
Sessions: id, user_id, dataset_id (nullable), incident_id (nullable), title, created_at.
Messages: id, session_id, role (USER/ASSISTANT), content, evidence_refs (JSON), model_name, prompt_version, created_at.

## audit_log
Fields: id, user_id (nullable), action_type, target_type, target_id, before_json, after_json, details, ip_addr, created_at (indexed).
