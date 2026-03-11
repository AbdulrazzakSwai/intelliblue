from scapy.all import rdpcap
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response, stream_with_context
from models import db, LogFile, Alert, ChatMessage
import csv
import re
import json
import requests
import os

app = Flask(__name__)

# Configure the SQLite database and upload folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///intelliblue.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Connect the database to the app
db.init_app(app)

# URL for your local Ollama instance
OLLAMA_URL = "http://localhost:11434/api/generate"

# Create the database tables before the first request
with app.app_context():
    db.create_all()

# --- WEB PAGE ROUTES ---

@app.route('/')
def dashboard():
    total_logs = LogFile.query.count()
    active_alerts = Alert.query.filter_by(status='Active').count()
    return render_template('dashboard.html', total_logs=total_logs, active_alerts=active_alerts)

@app.route('/logs')
def logs():
    all_logs = LogFile.query.order_by(LogFile.upload_date.desc()).all()
    return render_template('logs.html', logs=all_logs)

@app.route('/alerts')
def alerts():
    all_alerts = Alert.query.order_by(Alert.date_created.desc()).all()
    return render_template('alerts.html', alerts=all_alerts)

@app.route('/reports')
def reports():
    all_reports = Alert.query.order_by(Alert.date_created.desc()).all()
    return render_template('reports.html', reports=all_reports)

@app.route('/chat')
def chat():
    # Load chat history from the database
    history = ChatMessage.query.order_by(ChatMessage.timestamp.asc()).all()
    return render_template('chat.html', history=history)

# --- API ROUTES ---

@app.route('/api/chat', methods=['POST'])
def api_chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # 1. Save the User's message to the database immediately
    user_msg_record = ChatMessage(sender="User", text=user_message)
    db.session.add(user_msg_record)
    db.session.commit()

    # Make sure this is pushed all the way to the left
    system_prompt = """You are IntelliBlue, an expert Security Operations Center (SOC) AI assistant. 
Keep answers technical, clear, and professional.
Do not use introductory conversational filler phrases.
Start your technical answer immediately.
MUST USE single backticks (`) to highlight technical terms, IP addresses, file paths, and commands.
ALWAYS format lists using bullet points (* or -) with each item on a brand new line.
ALWAYS bold the key entity or title at the beginning of each bullet point.
ALWAYS end every single sentence and bullet point with a full stop (.)."""
    combined_prompt = f"{system_prompt}\n\nUser: {user_message}"

    payload = {
        "model": "llama3",
        "prompt": combined_prompt,
        "stream": True  # Streaming is enabled
    }

    # 2. Generator function to stream the response chunk-by-chunk
    def generate():
        full_ai_response = ""
        try:
            # Send request to local Ollama
            response = requests.post(OLLAMA_URL, json=payload, stream=True)
            
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    text_chunk = chunk.get("response", "")
                    full_ai_response += text_chunk
                    yield text_chunk  # Send the tiny piece of text to the frontend immediately
            
            # 3. Once the stream is finished, save the complete AI response to the database
            ai_msg_record = ChatMessage(sender="IntelliBlue", text=full_ai_response)
            db.session.add(ai_msg_record)
            db.session.commit()
            
        except Exception as e:
            yield f"\n[Connection Error: {str(e)}]"

    # Return the stream to the frontend
    return Response(stream_with_context(generate()), mimetype='text/plain')

def parse_security_file(filepath):
    """
    Automatically detects the file type and extracts readable text.
    Limits output to prevent LLM context window overflow.
    """
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    parsed_text = ""
    source_type = "RAW LOGS"

    try:
        if ext == '.csv':
            source_type = "SIEM/EDR CSV DATA"
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                parsed_text += f"Headers: {headers}\n"
                for i, row in enumerate(reader):
                    if i > 50: # Limit to first 50 rows
                        break
                    parsed_text += f"Row {i+1}: {row}\n"

        elif ext == '.json':
            source_type = "SIEM/EDR JSON DATA"
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convert back to a compact string, limiting size
                parsed_text = json.dumps(data, indent=2)[:5000] 

        elif ext in ['.pcap', '.pcapng']:
            source_type = "NETWORK PACKET CAPTURE (PCAP)"
            packets = rdpcap(filepath)
            for i, pkt in enumerate(packets):
                if i > 50: # Limit to first 50 packets
                    break
                parsed_text += f"Packet {i+1}: {pkt.summary()}\n"

        else:
            source_type = "RAW TEXT LOGS"
            with open(filepath, 'r', encoding='utf-8') as f:
                parsed_text = f.read(5000)

        return source_type, parsed_text

    except Exception as e:
        return "ERROR", f"Parsing failed: {str(e)}"

@app.route('/api/upload', methods=['POST'])
def api_upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    source_type, log_content = parse_security_file(filepath)

    if source_type == "ERROR":
        return jsonify({"error": log_content}), 500

    new_log = LogFile(filename=filename, source_type=source_type)
    db.session.add(new_log)
    db.session.commit()

    system_prompt = f"""You are IntelliBlue, an expert SOC AI. 
Analyze the following {source_type}. 
Identify any security threats, anomalies, or malicious activities.

CRITICAL INSTRUCTIONS:
- Do NOT include any introductory conversational text.
- Do NOT wrap your response in markdown code blocks or triple backticks (```).
- MUST USE single backticks (`) to highlight technical terms, IP addresses, URLs, file paths, and commands.
- SEVERITY RESTRICTION: You MUST only use one of these four levels: Informational, Low, Medium, or High.
- ALWAYS format items under IoCs and Mitigation as a bulleted list (using * or -).
- ALWAYS place each bullet point on a brand new line.
- ALWAYS bold the key entity or title at the beginning of each bullet point.
- ALWAYS end every single sentence and bullet point with a full stop (.).

Format your response as a formal Incident Report using Markdown.
Include these exact headings:
## Incident Summary
## Severity Level
## Indicators of Compromise (IoCs)
## Recommended Mitigation"""

    combined_prompt = f"{system_prompt}\n\n--- LOG DATA ---\n{log_content}\n--- END LOG DATA ---"

    payload = {
        "model": "llama3",
        "prompt": combined_prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        
        raw_result = response.json().get('response', 'Error generating report.')
        
        # Remove backticks but KEEP leading spaces for nested bullets
        analysis_result = raw_result.replace("```markdown", "").replace("```", "").strip()

        # Dynamically extract the severity level using regex
        severity_match = re.search(r'## Severity Level\s*\n+[^A-Za-z]*([A-Za-z]+)', analysis_result, re.IGNORECASE)
        parsed_severity = severity_match.group(1).capitalize() if severity_match else "Medium"

        new_alert = Alert(
            title=f"AI Detection: {filename}",
            description=analysis_result,
            severity=parsed_severity, # Now uses the dynamic severity
            status="Active"
        )
        db.session.add(new_alert)
        db.session.commit()

        return jsonify({"message": "Analysis complete", "alert_id": new_alert.id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)