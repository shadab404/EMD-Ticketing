import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

database_url = os.environ.get("DATABASE_URL")

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or "sqlite:///emdad.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# --- MODELS ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), default="employee")


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default="Open")
    priority = db.Column(db.String(50), default="Medium")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)

    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))

    def is_overdue(self):
        return self.due_date and self.due_date < datetime.utcnow()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# --- ROUTES ---

@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "success")
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    tickets = Ticket.query.all()

    total = len(tickets)
    open_tickets = Ticket.query.filter_by(status="Open").count()
    resolved = Ticket.query.filter(Ticket.status.in_(["Resolved", "Closed"])).count()
    overdue = len([t for t in tickets if t.is_overdue()])

    return render_template("dashboard.html",
                           tickets=tickets,
                           total=total,
                           open_tickets=open_tickets,
                           resolved=resolved,
                           overdue=overdue,
                           user=current_user)


@app.route('/create_ticket', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if request.method == "POST":
        title = request.form.get('title')
        description = request.form.get('description')
        priority = request.form.get('priority')

        ticket = Ticket(
            title=title,
            description=description,
            priority=priority
        )

        db.session.add(ticket)
        db.session.commit()

        flash("Ticket created successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template("create_ticket.html")


# --- DATABASE INIT ---
with app.app_context():
    db.create_all()

    if not User.query.filter_by(username="admin").first():
        hashed_pw = bcrypt.generate_password_hash("admin123").decode('utf-8')
        db.session.add(User(username="admin", password=hashed_pw, role="admin"))
        db.session.commit()


# --- RUN APP (for local only) ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
