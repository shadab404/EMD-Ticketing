from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))
    role = db.Column(db.String(50))

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    category = db.Column(db.String(100))
    priority = db.Column(db.String(50))
    status = db.Column(db.String(50), default="Open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_time = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    assigned_to = db.Column(db.String(100))

    def set_sla(self):
        hours = {"Low":48,"Medium":24,"High":8,"Critical":4}
        self.due_time = datetime.utcnow() + timedelta(hours=hours.get(self.priority,24))

    def is_overdue(self):
        return self.status not in ["Resolved","Closed"] and datetime.utcnow() > self.due_time

    def within_sla(self):
        return self.resolved_at and self.resolved_at <= self.due_time
