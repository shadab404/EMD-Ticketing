import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Ticket
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = "supersecret"

# PostgreSQL for Render
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")

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
            password=generate_password_hash("admin123"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form['username']).first()

        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid credentials")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
@login_required
def dashboard():
    low = Ticket.query.filter_by(priority="Low").count()
medium = Ticket.query.filter_by(priority="Medium").count()
high = Ticket.query.filter_by(priority="High").count()

    priority_filter = request.args.get("priority")
    status_filter = request.args.get("status")

    tickets = Ticket.query

    if priority_filter:
        tickets = tickets.filter_by(priority=priority_filter)

    if status_filter:
        tickets = tickets.filter_by(status=status_filter)

    tickets = tickets.all()

    total = Ticket.query.count()
    open_count = Ticket.query.filter_by(status="Open").count()
    resolved = Ticket.query.filter_by(status="Resolved").count()

    # Agent performance
    agents = User.query.filter_by(role="agent").all()
    performance = []

    for agent in agents:
        solved = Ticket.query.filter_by(agent_id=agent.id, status="Resolved").count()
        performance.append({"name": agent.username, "solved": solved})

    return render_template("dashboard.html",
                           tickets=tickets,
                           total=total,
                           open_count=open_count,
                           resolved=resolved,
                           performance=performance)


# ---------------- CREATE TICKET ----------------
@app.route("/create_ticket", methods=["GET","POST"])
@login_required
def create_ticket():

    if request.method == "POST":

        due = datetime.utcnow() + timedelta(days=2)  # SLA 2 days

        ticket = Ticket(
            title=request.form['title'],
            description=request.form['description'],
            priority=request.form['priority'],
            agent_id=request.form['agent'],
            due_date=due
        )

        db.session.add(ticket)
        db.session.commit()

        return redirect(url_for("dashboard"))

    agents = User.query.filter_by(role="agent").all()
    return render_template("create_ticket.html", agents=agents)


# ---------------- UPDATE STATUS ----------------
@app.route("/update/<int:id>/<status>")
@login_required
def update(id, status):
    ticket = Ticket.query.get_or_404(id)
    ticket.status = status

    if status == "Resolved":
        ticket.due_date = None

    db.session.commit()
    return redirect(url_for("dashboard"))
