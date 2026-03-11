from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize the database tool
db = SQLAlchemy()

class LogFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(150), nullable=False)
    source_type = db.Column(db.String(50)) # e.g., SIEM, IDS, EDR
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(50), default="Medium")
    status = db.Column(db.String(50), default="Active") # Can be 'Active', 'Resolved', 'Archived'
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50), nullable=False) # Will be 'User' or 'IntelliBlue'
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)