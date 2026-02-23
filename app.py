from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Ticket
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tickets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()

    if not User.query.filter_by(username="admin").first():
        admin = User(
            username="admin",
            password=generate_password_hash("admin123")
        )
        db.session.add(admin)
        db.session.commit()


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials")

    return render_template("login.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
@login_required
def dashboard():
    total = Ticket.query.count()
    open_tickets = Ticket.query.filter_by(status="Open").count()
    resolved = Ticket.query.filter_by(status="Resolved").count()
    overdue = Ticket.query.filter_by(status="Overdue").count()
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()

    return render_template("dashboard.html",
                           total=total,
                           open_tickets=open_tickets,
                           resolved=resolved,
                           overdue=overdue,
                           tickets=tickets)


# ---------------- CREATE TICKET ----------------
@app.route("/create_ticket", methods=["GET", "POST"])
@login_required
def create_ticket():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        priority = request.form.get("priority")
        assigned_to = request.form.get("assigned_to")

        ticket = Ticket(
            title=title,
            description=description,
            priority=priority,
            assigned_to=assigned_to,
            status="Open"
        )

        db.session.add(ticket)
        db.session.commit()
        return redirect(url_for("dashboard"))

    return render_template("create_ticket.html")


# ---------------- UPDATE STATUS ----------------
@app.route("/update_status/<int:id>/<status>")
@login_required
def update_status(id, status):
    ticket = Ticket.query.get_or_404(id)
    ticket.status = status
    db.session.commit()
    return redirect(url_for("dashboard"))


# ---------------- DELETE ----------------
@app.route("/delete_ticket/<int:id>")
@login_required
def delete_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    db.session.delete(ticket)
    db.session.commit()
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True)
