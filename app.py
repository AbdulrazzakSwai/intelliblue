from scapy.all import rdpcap
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response, stream_with_context, send_file
from models import db, LogFile, Alert, ChatSession, ChatMessage
import csv
import re
import json
import requests
import os
import uuid
import markdown
import io
from fpdf import FPDF, HTMLMixin

class PDF(FPDF, HTMLMixin):
    pass

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
        global_chat_sessions=ChatSession.query.order_by(ChatSession.date_created.desc()).all(),
        global_alerts=Alert.query.order_by(Alert.date_created.desc()).all()
    )

# Create the database tables before the first request
with app.app_context():
    db.create_all()

# --- WEB PAGE ROUTES ---

@app.route('/')
def dashboard():
    total_logs = LogFile.query.count()
    active_alerts = Alert.query.filter_by(status='Active').count()
    recent_alerts = Alert.query.order_by(Alert.date_created.desc()).limit(3).all()
    return render_template('dashboard.html', total_logs=total_logs, active_alerts=active_alerts, recent_alerts=recent_alerts)

@app.route('/logs')
def logs():
    all_logs = LogFile.query.order_by(LogFile.upload_date.desc()).all()
    return render_template('logs.html', logs=all_logs)

@app.route('/logs/clear', methods=['POST'])
def clear_logs():
    # 1. Delete physical files from the uploads folder
    folder = app.config['UPLOAD_FOLDER']
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}: {e}")
            
    # 2. Delete all log records from the database
    LogFile.query.delete()
    db.session.commit()
    return redirect(url_for('logs'))

@app.route('/api/check_alert/<path:filename>')
def check_alert(filename):
    alert = Alert.query.filter_by(title=f"Analysis of {filename}").first()
    if alert:
        if alert.status == 'Active':
            return jsonify({"status": "active"})
        else:
            return jsonify({"status": "archived"})
    return jsonify({"status": "deleted"})

@app.route('/alerts')
def alerts():
    active_alerts = Alert.query.filter_by(status="Active").order_by(Alert.date_created.desc()).all()
    return render_template('alerts.html', alerts=active_alerts)

@app.route('/reports')
def reports():
    archived_reports = Alert.query.filter_by(status="Resolved").order_by(Alert.date_created.desc()).all()
    return render_template('reports.html', reports=archived_reports)

@app.route('/alert/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    alert_to_resolve = Alert.query.get_or_404(alert_id)
    alert_to_resolve.status = "Resolved"
    db.session.commit()
    return redirect(url_for('alerts'))

@app.route('/report/<int:report_id>/restore', methods=['POST'])
def restore_alert(report_id):
    alert_to_restore = Alert.query.get_or_404(report_id)
    alert_to_restore.status = "Active"
    db.session.commit()
    return redirect(url_for('reports'))

@app.route('/report/<int:report_id>/export', methods=['GET'])
def export_report_pdf(report_id):
    alert = Alert.query.get_or_404(report_id)
    
    html_content = f"""
    <h1 align="center">{alert.title}</h1>
    <p><b>Date Generated:</b> {alert.date_created.strftime('%Y-%m-%d %H:%M UTC')}</p>
    <p><b>Severity Level:</b> <font color="{'red' if alert.severity == 'High' else 'orange' if alert.severity == 'Medium' else 'green' if alert.severity == 'Low' else 'blue'}">{alert.severity}</font> | <b>Status:</b> {alert.status}</p>
    <hr>
    """
    html_content += markdown.markdown(alert.description)
    
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=11)
    
    try:
        pdf.write_html(html_content)
    except Exception as e:
        # Fallback if html parsing fails natively for some weird character
        pdf.set_font("helvetica", size=11)
        pdf.multi_cell(0, 5, txt=f"Report: {alert.title}\nSeverity: {alert.severity}\n\n{alert.description}")
        
    pdf_bytes = pdf.output()
    
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"{re.sub(r'[^a-zA-Z0-9]', '_', alert.title)}.pdf"
    )

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
    # Check if there is already an empty session to prevent spamming empty chats
    empty_session = None
    for session in ChatSession.query.order_by(ChatSession.date_created.desc()).all():
        if ChatMessage.query.filter_by(session_id=session.id).count() == 0:
            empty_session = session
            break
            
    if empty_session:
        session_id = empty_session.id
    else:
        session_id = str(uuid.uuid4())
        new_session = ChatSession(id=session_id, title="New Chat")
        db.session.add(new_session)
        db.session.commit()
    
    # Optional URL argument to immediately attach an alert constraint to default chat window
    alert_id = request.args.get('alert_id')
    if alert_id:
        return redirect(url_for('chat', session_id=session_id, auto_alert=alert_id))
        
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

@app.route('/chat/<session_id>/delete', methods=['POST'])
def delete_chat(session_id):
    ChatMessage.query.filter_by(session_id=session_id).delete()
    session_to_delete = ChatSession.query.get_or_404(session_id)
    db.session.delete(session_to_delete)
    db.session.commit()
    return redirect(url_for('chat_redirect'))

@app.route('/report/<int:report_id>/delete', methods=['POST'])
def delete_report(report_id):
    report_to_delete = Alert.query.get_or_404(report_id)
    db.session.delete(report_to_delete)
    db.session.commit()
    return redirect(url_for('reports'))

# --- API ROUTES ---

@app.route('/api/chat', methods=['POST'])
def api_chat():
    user_message = request.json.get('message')
    session_id = request.json.get('session_id', 'default')
    alert_id = request.json.get('alert_id')
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Expand the user message with the attached alert's full context if one was provided
    final_user_message = user_message
    if alert_id:
        alert = Alert.query.get(alert_id)
        if alert:
            final_user_message += f"\n\n*(Attached Reference: {alert.title})*\n\n> **Severity Level**: {alert.severity}\n> \n> {alert.description}"

    # (We wait to rename the session until after the AI responds)
    session = ChatSession.query.get(session_id)
    if session and session.title == "New Chat":
        # Temporarily set to something else so we know it's pending a real title
        session.title = "Generating Title..."
        db.session.commit()

    # 1. Save the User's message to the database immediately
    user_msg_record = ChatMessage(sender="User", text=final_user_message, session_id=session_id)
    db.session.add(user_msg_record)
    db.session.commit()

    # Retrieve context: grab the last 10 messages (including this new one) from the DB
    history_records = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp.asc()).all()
    # Keep it limited so the context window to Ollama doesn't overflow over time
    history_records = history_records[-10:] 
    
    chat_context = ""
    for msg in history_records:
        chat_context += f"{msg.sender}: {msg.text}\n"

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
    
    combined_prompt = f"{system_prompt}\n\n--- Conversation History ---\n{chat_context}IntelliBlue:"

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
                title_prompt = f"""You are an assistant that creates extremely concise titles (3 to 4 words max) for chat conversations.
Read the following exchange and provide ONLY the title, no quotes, no extra text, no markdown, no asterisks, no hashtags.
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
                        raw_title = title_resp.json().get('response', '').strip()
                        # Scrub all markdown and extra characters entirely
                        smart_title = re.sub(r'[*_#`~>\[\]]', '', raw_title).strip().replace('"', '').replace("'", "")
                        # Let CSS truncation handle lengths, but hard limit it too just in case
                        if len(smart_title) > 40:
                            smart_title = smart_title[:37] + "..."
                            
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
                # 1. Strip markdown characters first from the 3 pulled words
                clean_words = [re.sub(r'[*_#`~>\[\]]', '', word) for word in words[:3]]
                # 2. Capitalize the clean words so actual letters are hit, not asterisks
                capitalized_words = [word.capitalize() for word in clean_words if word]
                
                fallback_title = " ".join(capitalized_words) + ("..." if len(words) > 3 else "")
                
                # Protect database width logic identically to non-fallback mode
                if len(fallback_title) > 40:
                    fallback_title = fallback_title[:37] + "..."
                    
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

        elif ext == '.log':
            source_type = "SYSTEM EVENT LOGS"
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                parsed_text = f.read(5000)

        else:
            source_type = "RAW TEXT LOGS"
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
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
    name, ext = os.path.splitext(original_filename)
    
    # Generate a robust unique identifier to prevent any naming collisions
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{name}_{unique_id}{ext}"
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
        
        # Clean up the physical file from the server now that analysis is complete
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as delete_error:
            print(f"Warning: Failed to delete physical log file {filepath}: {delete_error}")

        return jsonify({"message": "Analysis complete", "alert_id": new_alert.id, "filename": filename}), 200

    except Exception as e:
        # Guarantee cleanup even if Ollama request completely crashes
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)