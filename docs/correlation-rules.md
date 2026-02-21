# Correlation Rules

## Rule 1: Brute Force / Password Spraying

**Trigger**: 5+ login failures within a 10-minute window from the same `src_ip` OR targeting the same `username`.

**Logic**:
1. Query all `login_failure` events for the dataset
2. Slide a time window (default 10min) over grouped events
3. If count ≥ threshold: create/update incident
4. Cross-correlate with IDS alerts and web 401s from same IP to boost confidence

**Confidence scoring**:
- Base: 40 (IP-based) or 50 (username-based)
- +20 if IDS alerts from same IP within window
- +15 if web 401 spikes from same IP
- Cap: 95

## Rule 2: Web Scanning / Reconnaissance

**Trigger**: 15+ unique URL hits within 5 minutes OR 10+ 4xx errors within 5 minutes from same IP.

**Logic**:
1. Query all web events (source_type=WEB_LOG)
2. Flag suspicious user agents (Nikto, sqlmap, nmap, dirbuster, etc.)
3. Slide time window over per-IP events
4. If URL count or error count ≥ threshold: create incident

**Confidence scoring**:
- Base: 50
- +20 if suspicious user agent detected
- +15 if IDS alert from same IP

## Rule 3: IDS Confirmed Alert

**Trigger**: Any IDS alert (from Suricata or Snort).

**Logic**:
1. Each IDS alert seeds an incident (or adds to existing if same rule/IP combo)
2. Pull auth and web events within ±10 minutes for corroboration
3. Severity mapped from IDS priority (1=CRITICAL, 2=HIGH, 3=MEDIUM, 4=LOW)

**Confidence scoring**:
- Base: 65
- +15 if auth events corroborate
- +10 if web events corroborate

## Idempotency

All rules check for existing incidents before creating new ones to prevent duplicates on re-runs.

## Configuration

Edit `config/correlation_config.json`:
```json
{
  "brute_force_window_minutes": 10,
  "brute_force_threshold": 5,
  "web_scan_window_minutes": 5,
  "web_scan_url_threshold": 15,
  "web_scan_error_threshold": 10,
  "ids_correlation_window_minutes": 10
}
```
