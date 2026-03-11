from scapy.all import rdpcap
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response, stream_with_context
from models import db, LogFile, Alert, ChatSession, ChatMessage
import csv
import re
import json
import requests
import os
import uuid

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

# Inject global variables into all templates (like base.html)
@app.context_processor
def inject_global_data():
    return dict(
        global_chat_sessions=ChatSession.query.order_by(ChatSession.date_created.desc()).all()
    )

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
def chat_redirect():
    # If no sessions exist, create a default one to preserve old messages
    # and redirect to latest session
    latest_session = ChatSession.query.order_by(ChatSession.date_created.desc()).first()
    if not latest_session:
        return redirect(url_for('new_chat'))
    return redirect(url_for('chat', session_id=latest_session.id))

@app.route('/chat/new')
def new_chat():
    session_id = str(uuid.uuid4())
    new_session = ChatSession(id=session_id, title="New Chat")
    db.session.add(new_session)
    db.session.commit()
    return redirect(url_for('chat', session_id=session_id))

@app.route('/chat/<session_id>')
def chat(session_id):
    sessions = ChatSession.query.order_by(ChatSession.date_created.desc()).all()
    active_session = ChatSession.query.get_or_404(session_id)
    
    # Load chat history from the database for this session
    history = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp.asc()).all()
    
    # Pre-populate a fake welcoming message if history is empty
    if not history:
        welcoming_msg = {
            'sender': 'IntelliBlue',
            'text': "Welcome to IntelliBlue Chat. I am your expert SOC Assistant. You can ask me to explain specific alerts, draft mitigation steps, or analyze security concepts. How can I help you today?"
        }
        history = [welcoming_msg]

    return render_template('chat.html', history=history, sessions=sessions, active_session=active_session)

# --- API ROUTES ---

@app.route('/api/chat', methods=['POST'])
def api_chat():
    user_message = request.json.get('message')
    session_id = request.json.get('session_id', 'default')
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # (We wait to rename the session until after the AI responds)
    session = ChatSession.query.get(session_id)
    if session and session.title == "New Chat":
        # Temporarily set to something else so we know it's pending a real title
        session.title = "Generating Title..."
        db.session.commit()

    # 1. Save the User's message to the database immediately
    user_msg_record = ChatMessage(sender="User", text=user_message, session_id=session_id)
    db.session.add(user_msg_record)
    db.session.commit()

    # Make sure this is pushed all the way to the left
    system_prompt = """You are IntelliBlue, an expert Security Operations Center (SOC) AI assistant. 
Keep answers technical, clear, and professional, but keep a polite and active tone if the user responded with a greeting or casual message.
Do not use introductory conversational filler phrases.
Start your technical answer immediately.
MUST USE single backticks (`) to highlight technical terms, IP addresses, file paths, and commands.
CRITICAL: Defang all IP addresses and URLs using brackets. Example: 192.168.1.1 becomes 192[.]168[.]1[.]1 and http://evil.com becomes http[://]evil[.]com.
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
        generated_title = None
        try:
            # Send request to local Ollama
            response = requests.post(OLLAMA_URL, json=payload, stream=True)
            
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    text_chunk = chunk.get("response", "")
                    full_ai_response += text_chunk
                    yield text_chunk  # Send the tiny piece of text to the frontend immediately
            
            # Send a secret signal asserting that the AI has explicitly finished its regular message stream
            yield "|||END_STREAM|||"

            # Check if this is the first exchange before the finally block so we can yield it
            session = ChatSession.query.get(session_id)
            # The AI msg is not added to DB yet, so count is 1 (just the user msg)
            msg_count = ChatMessage.query.filter_by(session_id=session_id).count() 
            
            if session and msg_count == 1:
                title_prompt = f"""You are an assistant that creates extremely concise titles (3 to 6 words max) for chat conversations.
Read the following exchange and provide ONLY the title, no quotes, no extra text.
User: {user_message}
AI: {full_ai_response}"""
                title_payload = {
                    "model": "llama3",
                    "prompt": title_prompt,
                    "stream": False
                }
                try:
                    title_resp = requests.post(OLLAMA_URL, json=title_payload)
                    if title_resp.status_code == 200:
                        smart_title = title_resp.json().get('response', '').strip().replace('"', '').replace("'", "")
                        if smart_title:
                            session.title = smart_title
                            db.session.commit()
                            generated_title = smart_title
                            yield f"|||TITLE|||{smart_title}"
                except Exception as title_e:
                    print(f"Failed to generate title: {title_e}")
                    
        except GeneratorExit:
            # Client closed the connection (User interrupted)
            full_ai_response += "\n\n*(user interruption)*"
            
            # Since the user interrupted, we should assign a fallback title instead of waiting on LLM
            session = ChatSession.query.get(session_id)
            if session and session.title == "Generating Title...":
                words = user_message.split()
                # Capitalize the first letter of each of the first 3 words
                capitalized_words = [word.capitalize() for word in words[:3]]
                fallback_title = " ".join(capitalized_words) + ("..." if len(words) > 3 else "")
                session.title = fallback_title
                db.session.commit()
                # Instead of yielding here (which fails because the stream is already disconnected due to GeneratorExit),
                # we just safely store it to the database so that when the user refreshes, the title is correct.
                
        except Exception as e:
            error_msg = f"\n[Connection Error: {str(e)}]"
            full_ai_response += error_msg
            yield error_msg
        finally:
            # 3. Once the stream is finished or interrupted, save the AI response to the database
            try:
                ai_msg_record = ChatMessage(sender="IntelliBlue", text=full_ai_response, session_id=session_id)
                db.session.add(ai_msg_record)
                db.session.commit()
            except Exception as db_e:
                print(f"Failed to save to database: {db_e}")

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

    original_filename = secure_filename(file.filename)
    filename = original_filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Handle duplicate filenames
    counter = 1
    name, ext = os.path.splitext(original_filename)
    while os.path.exists(filepath):
        counter += 1
        filename = f"{name}_{counter}{ext}"
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
- CRITICAL: Defang all IP addresses and URLs using brackets. Example: 192.168.1.1 becomes 192[.]168[.]1[.]1 and http://evil.com becomes http[://]evil[.]com.
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
            title=f"Analysis of {filename}",
            description=analysis_result,
            severity=parsed_severity, # Now uses the dynamic severity
            status="Active"
        )
        db.session.add(new_alert)
        db.session.commit()

        return jsonify({"message": "Analysis complete", "alert_id": new_alert.id, "filename": filename}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)