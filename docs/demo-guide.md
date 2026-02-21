# Demo Guide

## Setup (5 minutes)

```bash
# Start services
make setup
make postgres    # starts PostgreSQL in Docker
make db-migrate
make seed        # creates users + uploads sample data
```

## Demo Flow

### 1. Login (2 min)
- Open http://localhost:5173
- Login as `admin / admin123`
- Show role-based navigation (Admin sees all menu items)

### 2. Dataset Overview (2 min)
- Navigate to **Datasets**
- Show the "Demo Dataset - January 2024" with READY status
- Click to see event count and incident count
- Note the parse_errors field (should be empty for clean demo data)

### 3. Incident List (3 min)
- Navigate to **Incidents**
- Show incidents filtered by severity:
  - CRITICAL: IDS-confirmed privilege escalation attempts
  - HIGH: Brute force from 192.168.1.150
  - MEDIUM: Web scanning (Nikto)
- Filter by status: NEW vs ACK

### 4. Incident Detail - Brute Force (5 min)
- Click on the brute force incident
- Show: timeline of login failures, rule explanation, confidence 70%+
- Click **AI Summary** (if LLM configured) - shows structured JSON analysis
- Add a triage note: "Confirmed brute force from internal IP 192.168.1.150"
- **Acknowledge** the incident

### 5. RBAC Demo (2 min)
- Open new incognito window, login as `analyst1 / analyst123` (L1)
- Show L1 can view and acknowledge
- Show L1 CANNOT close incidents (button grayed/hidden)
- Login as `analyst2 / analyst123` (L2)
- Show L2 CAN close incidents

### 6. Chat Demo (3 min)
- Navigate to **Chat**
- Create new session, select the demo dataset
- Ask: "What IPs were involved in attacks?"
- Ask: "What brute force activity happened?"
- Show evidence references in response

### 7. Admin Features (2 min)
- Login as admin
- Show **Audit Log** - all actions logged
- Show **User Management** - create/disable users
- Show **Retention** - delete datasets (don't delete during demo!)

### 8. PDF Export (1 min)
- Open incident detail
- Click **PDF** button
- Show generated PDF with timeline, evidence, AI summary

## Key Talking Points

1. **Fully offline** - No internet connection required during operation
2. **Explainable correlation** - Every incident shows which rule fired and why
3. **RBAC** - Strict role enforcement, L1 can't close incidents
4. **Audit trail** - Every action recorded with user, timestamp, IP
5. **Streaming-ready** - Architecture supports adding real-time log tailing without rewrite
6. **LLM optional** - System fully functional without AI (graceful degradation)
