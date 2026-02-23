import os
from datetime import datetime, timedelta
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message

# ---------------- APP CONFIG ----------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'

# PostgreSQL for Render
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Email Config (CHANGE THESE)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_app_password'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
mail = Mail(app)

# ---------------- MODELS ----------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20), default="agent")

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    priority = db.Column(db.String(20))
    status = db.Column(db.String(20), default="Open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    attachment = db.Column(db.String(200))
    agent_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    department = db.Column(db.String(100))
    email = db.Column(db.String(100))

# ---------------- LOGIN ----------------
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

# ---------------- ROUTES ----------------
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

    if current_user.role == "agent":
        tickets = Ticket.query.filter_by(agent_id=current_user.id).all()
    else:
        tickets = Ticket.query.all()

    total = Ticket.query.count()
    open_count = Ticket.query.filter_by(status="Open").count()
    resolved = Ticket.query.filter_by(status="Resolved").count()

    low = Ticket.query.filter_by(priority="Low").count()
    medium = Ticket.query.filter_by(priority="Medium").count()
    high = Ticket.query.filter_by(priority="High").count()

    return render_template("dashboard.html",
                           tickets=tickets,
                           total=total,
                           open_count=open_count,
                           resolved=resolved,
                           low=low,
                           medium=medium,
                           high=high)

# ---------------- CREATE TICKET ----------------
@app.route("/create_ticket", methods=["GET","POST"])
@login_required
def create_ticket():

    if request.method == "POST":

        file = request.files.get("attachment")
        filename = None

        if file:
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        due = datetime.utcnow() + timedelta(days=2)

        ticket = Ticket(
            title=request.form['title'],
            description=request.form['description'],
            priority=request.form['priority'],
            agent_id=request.form['agent'],
            due_date=due,
            attachment=filename
        )

        db.session.add(ticket)
        db.session.commit()

        # Email Notification
        try:
            msg = Message("New Ticket Created",
                          sender=app.config['MAIL_USERNAME'],
                          recipients=[app.config['MAIL_USERNAME']])
            msg.body = f"New Ticket: {ticket.title}"
            mail.send(msg)
        except:
            pass

        return redirect(url_for("dashboard"))

    agents = User.query.filter_by(role="agent").all()
    return render_template("create_ticket.html", agents=agents)

# ---------------- UPDATE STATUS ----------------
@app.route("/update/<int:id>/<status>")
@login_required
def update_status(id, status):
    ticket = Ticket.query.get_or_404(id)
    ticket.status = status
    db.session.commit()
    return redirect(url_for("dashboard"))

# ---------------- ADMIN PANEL ----------------
@app.route("/admin")
@login_required
def admin_panel():
    if current_user.role != "admin":
        return "Access Denied"

    users = User.query.all()
    return render_template("admin.html", users=users)

# ---------------- EMPLOYEES ----------------
@app.route("/employees")
@login_required
def employees():
    employees = Employee.query.all()
    return render_template("employees.html", employees=employees)

# ---------------- LANGUAGE SWITCH ----------------
@app.route("/change_lang/<lang>")
def change_lang(lang):
    session['lang'] = lang
    return redirect(request.referrer or url_for("dashboard"))

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
