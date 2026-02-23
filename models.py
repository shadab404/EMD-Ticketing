from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(50), default="employee")  # admin / agent / employee
    language = db.Column(db.String(10), default="en")

    tickets_created = db.relationship("Ticket", backref="creator", foreign_keys='Ticket.created_by')
    tickets_assigned = db.relationship("Ticket", backref="agent", foreign_keys='Ticket.assigned_to')


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    priority = db.Column(db.String(50))
    status = db.Column(db.String(50), default="Open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sla_deadline = db.Column(db.DateTime)
    attachment = db.Column(db.String(300))

    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"))
