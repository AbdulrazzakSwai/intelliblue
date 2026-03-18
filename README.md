<p align="center">
  <img src="assets/intelliblue_logo.png" alt="IntelliBlue Logo" width="120"/>
</p>

<h1 align="center">IntelliBlue</h1>

<p align="center">
  <b>AI-Powered Security Operations Center Platform</b><br>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Flask-3.0-lightgrey?logo=flask" alt="Flask"/>
  <img src="https://img.shields.io/badge/LLM-Llama_3_&_3.2-green?logo=meta" alt="Llama 3"/>
  <img src="https://img.shields.io/badge/Ollama-Local_AI-black?logo=ollama" alt="Ollama"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License"/>
</p>

---

## Table of Contents

1. [About the Project](#about-the-project)
2. [Features](#features)
   - [AI Chatbot](#ai-chatbot)
   - [Smart Log Analysis](#smart-log-analysis)
   - [Integrated Capabilities](#integrated-capabilities)
3. [Tech Stack](#tech-stack)
4. [Installation](#installation)
   - [Windows (Automated)](#windows-automated-install)
   - [Linux (Automated)](#linux-automated-install)
   - [Manual Installation](#manual-installation)
5. [Usage Guide](#usage-guide)
   - [Dashboard](#dashboard)
   - [Uploading & Analyzing Logs](#uploading--analyzing-logs)
   - [Managing Alerts](#managing-alerts)
   - [Chatting with the AI Assistant](#chatting-with-the-ai-assistant)
   - [Reports & Exports](#reports--exports)
   - [Test Files](#test-files)
6. [Security Considerations](#security-considerations)

---

## About the Project

**IntelliBlue** is a fully local, AI-powered Security Operations Center (SOC) platform designed for cybersecurity analysts, students, and enthusiasts. It combines a modern web dashboard with a locally-hosted Large Language Model (Llama 3 and 3.2 via Ollama) to deliver real-time threat analysis, interactive incident investigation, and structured incident reporting.

### What It Does

- **Automated Log Analysis** — Upload SIEM exports, EDR telemetry, firewall logs, or packet captures and receive a comprehensive AI-generated Incident Report complete with an executive summary, severity rating, IOC extraction, MITRE ATT&CK mapping, impact assessment, and remediation steps.
- **SOC AI Assistant** — A conversational chatbot with deep cybersecurity expertise. Ask it to explain alerts, draft mitigation plans, analyze threat intelligence, or investigate indicators of compromise. It remembers conversation context and can reference any active alert.
- **Alert Triage Workflow** — Manage alerts through a full lifecycle: Active → Resolved or False Positive, with severity filtering, PDF export, and one-click restoration.
- **Dashboard Overview** — A real-time SOC dashboard showing ingested log counts, active alert totals, AI engine status, and recent alerts at a glance.

### Underlying Infrastructure

| Layer               | Technology                                         |
| ------------------- | -------------------------------------------------- |
| **Backend**         | Flask 3.0, Flask-SQLAlchemy, Python 3.10+          |
| **Database**        | SQLite (local, zero-config)                        |
| **AI Engine**       | Ollama running Llama 3 & Llama 3.2 locally         |
| **Network Parsing** | Scapy (PCAP/PCAPNG analysis)                       |
| **PDF Generation**  | fpdf2 with HTML rendering                          |
| **Frontend**        | Tailwind CSS, Marked.js, DOMPurify, Font Awesome 6 |
| **Fonts**           | Space Grotesk (headings), Inter (body)             |

---

## Features

### AI Chatbot

| Feature                          | Description                                                                                                                                                                |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Streaming Responses**          | AI responses are streamed in real time with a smooth typewriter effect — no waiting for the full answer to generate.                                                       |
| **Response Interruption**        | A STOP button lets you halt the AI mid-response if you already have what you need.                                                                                         |
| **Regenerate Response**          | Didn't like the answer? A "Resend Last Prompt" button re-sends your last message with higher creativity for a fresh response.                                              |
| **Conversation Memory**          | The AI remembers the last 10 messages in each session for contextual follow-up questions and multi-turn investigations.                                                      |
| **Markdown Rendering**           | Responses are rendered with full Markdown support — code blocks, tables, bold, lists — sanitized via DOMPurify for safety.                                                 |
| **Smart Chat Titles**            | After your first exchange, the AI auto-generates a concise 3–6 word title for the chat (e.g., "Phishing Email Analysis") in the background without blocking your workflow. |
| **Session Management**           | Create unlimited chat sessions, switch between them from the sidebar, and delete sessions you no longer need.                                                              |
| **Welcome Message**              | Every new chat opens with an animated welcome message from the AI assistant.                                                                                               |
| **Duplicate Session Prevention** | The app won't let you create a new empty chat if one already exists — keeps your sidebar clean.                                                                            |

### Smart Log Analysis

| Feature                          | Description                                                                                                                                                                                      |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Multi-Format Support**         | Upload and analyze `.csv`, `.json`, `.pcap`, `.pcapng`, `.log`, and `.txt` security log files.                                                                                                   |
| **Structured Incident Reports**  | Every analysis produces a formal report with: Executive Summary, Severity Level, Artifact Details, Analysis Findings, IOCs, Impact Assessment, Remediation Steps, and False Positive Assessment. |
| **IOC Defanging**                | All IP addresses and URLs in reports are automatically defanged (e.g., `1.2.3.4` → `1[.]2[.]3[.]4`) to prevent accidental clicks.                                                                |
| **MITRE ATT&CK Mapping**         | Reports reference MITRE ATT&CK technique IDs (e.g., T1059.001) where applicable.                                                                                                                 |
| **Automatic Severity Detection** | The AI assigns a severity level (Critical, High, Medium, Low) and the system extracts it to categorize the alert.                                                                                |
| **Cancel Analysis**              | Changed your mind? Cancel an in-progress analysis and the system cleans up gracefully.                                                                                                           |
| **Auto-Cleanup**                 | Uploaded log files are automatically deleted from the server after analysis completes — only the report is kept.                                                                                 |
| **Upload History**               | A timestamped history of all analyzed files with quick links to view the resulting alert.                                                                                                        |
| **Smart Filename Handling**      | Files are timestamped on upload to avoid collisions. Source type is auto-detected from the file extension.                                                                                       |

### Integrated Capabilities

| Feature                        | Description                                                                                                                                                                                             |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Dynamic Local Model Swapping**   | On the fly, change which active local model serves as your primary AI engine inside the top nav. You are free to pick between **Thinking mode** (for complex tasks) and **Fast mode** (for quick responses). |
  | **Chat About Any Alert**       | From the Alerts page, click "Investigate with AI" to open a new chat session with the full alert context pre-loaded. Ask follow-up questions, request mitigation steps, or challenge the AI's findings. |
| **Alert Lifecycle Management** | Move alerts through a full workflow: **Active** → **Resolved** (archived) or **False Positive** (with analyst reasoning). Restore any archived alert back to Active if needed.                          |
| **PDF Report Export**          | Export any alert or archived report as a professionally formatted PDF document with severity color-coding and Markdown-rendered content.                                                                |
| **Severity-Sorted Alerts**     | Active alerts are auto-sorted by severity: Critical → High → Medium → Low, so the most urgent threats are always at the top.                                                                            |
| **Advanced Filtering**         | Filter alerts and reports by severity level and file type for quick triage.                                                                                                                             |
| **False Positive Workflow**    | Mark alerts as false positives with an optional reason. False positives are archived separately in the Reports page for audit trail purposes.                                                           |
| **Real-Time Dashboard**        | The dashboard shows live counts of total ingested logs, active alerts, AI engine status, and the three most recent alerts with severity badges and direct links.                                        |
| **Deleted Alert Detection**    | If a log's corresponding alert was deleted, clicking "View Alert" in the logs page shows a graceful animated notification instead of an error.                                                          |
| **Security-First Design**      | Secure filename handling, file extension whitelisting, input sanitization (DOMPurify), prompt injection protection, parameterized DB queries, and automatic temp file cleanup.                          |
| **100% Offline Capable**       | Runs entirely locally on your machine. No internet connection, cloud APIs, or external telemetry required, ensuring complete data privacy for sensitive security logs.                                  |

---

## Tech Stack

```
Backend:    Flask 3.0 · Flask-SQLAlchemy · SQLite · Python 3.10+
AI:         Ollama · Llama 3 & Llama 3.2 · Streaming API
Parsing:    Scapy (PCAP) · csv/json (structured logs)
Frontend:   Tailwind CSS · Marked.js · DOMPurify · Font Awesome 6
PDF:        fpdf2 with HTML-to-PDF rendering
Security:   Werkzeug · DOMPurify · Prompt injection guards
```

---

## Installation

> **⚠️ WARNING:** Installing and running IntelliBlue inside a Virtual Machine (VM) is highly discouraged. Running local Large Language Models inside a VM without dedicated GPU power will result in severely degraded performance and extremely slow AI response times.

> **ℹ️ NOTE:** Installation may take a while because the Llama models are nearly 7GB in size.

### Windows (Automated Install)

Open PowerShell **as Administrator** and run the following command to download and execute the installation script in one step:

```powershell
iwr https://raw.githubusercontent.com/AbdulrazzakSwai/IntelliBlue/main/assets/installation-scripts/windows_install.ps1 -UseBasicParsing | iex
```

This script will automatically:

1. Verify Administrator privileges
2. Install Git, Python 3.12, Ollama, and Npcap (if missing)
3. Download the Llama models via Ollama
4. Clone the repository to the `%USERPROFILE%\Desktop\IntelliBlue` folder
5. Create a virtual environment and install all dependencies
6. Prompt you to launch the app immediately

### Linux (Automated Install)

Run the following command in your terminal. You may be prompted for your `sudo` password to install system packages.

```bash
curl -fsSL https://raw.githubusercontent.com/AbdulrazzakSwai/IntelliBlue/main/assets/installation-scripts/linux_install.sh | bash
```

This script will automatically:

1. Detect your package manager (apt, dnf, pacman)
2. Install Git, Python 3 (with pip/venv), Ollama, and `libpcap` (if missing)
3. Download the Llama models via Ollama
4. Clone the repository to the `~/Desktop/IntelliBlue` directory
5. Create a Python virtual environment and install all dependencies
6. Prompt you to launch the app immediately

### Manual Installation

If you prefer to install everything yourself:

```bash
# 1. Install Git, Python 3.10+, and Ollama from their official websites
#    Windows users: also install Npcap from https://npcap.com
#    Linux users: also install libpcap (e.g., sudo apt install libpcap-dev)

# 2. Clone the repository and navigate into it
git clone https://github.com/AbdulrazzakSwai/IntelliBlue.git
cd IntelliBlue

# 3. Pull the Llama models
ollama pull llama3
ollama pull llama3.2

# 4. Create and activate a virtual environment
# Windows (Powershell):
python -m venv venv
Set-ExecutionPolicy Bypass -Scope Process; . .\venv\Scripts\Activate
# Linux/macOS:
python3 -m venv venv
source venv/bin/activate

# 5. Install Python dependencies
pip install -r requirements.txt

# 6. Run the application
python app.py
```

The app will be available at **http://localhost:5000**.

---

## Usage Guide

### Dashboard

The dashboard is your SOC overview at a glance:

- **Total Logs Ingested** — Count of all log files that have been analyzed.
- **Active Alerts** — Number of unresolved alerts awaiting triage.
- **AI Engine Core** — Shows the active LLM model and system status.
- **Recent Alerts** — The three most recent alerts with severity badges. Click any alert to jump to its details.
- **Quick Actions** — "Upload Logs" and "Ask AI Assistant" buttons for fast navigation.

### Uploading & Analyzing Logs

1. Navigate to **Log Management** from the sidebar.
2. Click the upload area or drag and drop a security log file.
   - Supported formats: `.csv`, `.json`, `.pcap`, `.pcapng`, `.log`, `.txt`
3. Click **Analyze with IntelliBlue**.
4. The AI will parse and analyze the file — this may take a moment depending on file size and hardware.
   - You can **cancel** the analysis at any time using the cancel button.
5. Once complete, an animated success message appears with a link to the generated alert.
6. The physical log file is automatically deleted after analysis — only the AI report is retained.

### Managing Alerts

Navigate to **Active Alerts** to see all unresolved threats, sorted by severity:

- **Filter** alerts by severity (Critical, High, Medium, Low) or file type.
- **Resolve** — Archives the alert under "Resolved" in the Reports page.
- **False Positive** — Archives the alert as a false positive with an optional analyst reason.
- **Investigate with AI** — Opens a new chat session with the full alert context pre-attached, so you can ask follow-up questions.
- **Export PDF** — Downloads a formatted PDF of the incident report.

### Chatting with the AI Assistant

1. Click **+ New Chat** in the sidebar, or click "Ask AI Assistant" on the dashboard.
2. Type your question or paste indicators of compromise for analysis.
3. The AI streams its response in real time with Markdown formatting.
4. Use the **STOP** button to interrupt a response, or the **Regenerate** button to get a fresh answer.
5. Previous messages are retained in the session — ask follow-up questions naturally.
6. To investigate a specific alert, use the "Investigate with AI" button on the Alerts page, or attach an alert from within the chat.

### Reports & Exports

Navigate to **Archived Reports** to manage completed investigations:

- **Resolved Reports** — Alerts marked as resolved, with full report content.
- **False Positives** — Alerts flagged as false positives, with the analyst's reasoning.
- **Restore** — Move any archived report back to Active Alerts if you need to re-investigate.
- **Export PDF** — Download a formatted PDF of any report.
- **Delete** — Permanently remove a report from the database.

### Test Files

IntelliBlue ships with sample security log files in the `assets/test-files/` directory for you to try out the analysis feature:

| File                   | Type | Description                                                    |
| ---------------------- | ---- | -------------------------------------------------------------- |
| `firewall_traffic.csv` | CSV  | Firewall traffic log data with network connections             |
| `edr_ransomware.json`  | JSON | EDR telemetry data containing ransomware-related events        |
| `c2_beacon.pcap`       | PCAP | Network packet capture with command-and-control beacon traffic |
| `auth_secure.txt`      | TXT  | Authentication and access control log entries                  |
| `web_access.log`       | LOG  | Web server access logs with HTTP requests                      |

Upload any of these files from the **Log Management** page to see IntelliBlue generate a full incident analysis report.

---

## Security Considerations

IntelliBlue implements multiple layers of security:

- **File Upload Safety** — Extension whitelisting, secure filename sanitization via Werkzeug, and automatic deletion of uploaded files post-analysis.
- **Prompt Injection Protection** — User-supplied data is wrapped in designated tags and the system prompt explicitly instructs the AI to treat it as passive data, not executable instructions.
- **IOC Defanging** — All IP addresses and URLs in AI outputs are defanged to prevent accidental navigation to malicious infrastructure.
- **Output Sanitization** — All AI-generated Markdown is rendered via Marked.js and sanitized through DOMPurify before being injected into the DOM.
- **Database Security** — All queries use SQLAlchemy's ORM with parameterized statements, preventing SQL injection. Alert IDs use random UUIDs.
- **No Cloud Dependencies** — The AI model runs entirely on your local machine via Ollama. No data is transmitted externally.

---

<p align="center">
  <b>IntelliBlue</b> — Your Local AI-Powered SOC Analyst<br>
  <sub>Built with Flask · Powered by Llama Models · Secured by Design</sub>
</p>




