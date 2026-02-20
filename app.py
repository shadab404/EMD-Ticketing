import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask_bcrypt import Bcrypt

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-dev-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    "DATABASE_URL", "sqlite:///emdad.db"
)
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

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default="Open")

    def is_overdue(self):
        return False

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))

    return render_template("login.html")

@app.route('/')
@login_required
def dashboard():
    tickets = Ticket.query.all()
    total = len(tickets)
    open_tickets = Ticket.query.filter_by(status="Open").count()
    resolved = Ticket.query.filter(Ticket.status.in_(["Resolved", "Closed"])).count()
    overdue = len([t for t in tickets if t.is_overdue()])

    return render_template("dashboard.html",
                           total=total,
                           open_tickets=open_tickets,
                           resolved=resolved,
                           overdue=overdue,
                           tickets=tickets)

# --- DATABASE INIT (IMPORTANT FOR RENDER) ---
with app.app_context():
    db.create_all()

    if not User.query.filter_by(username="admin").first():
        hashed_pw = bcrypt.generate_password_hash("admin123").decode('utf-8')
        db.session.add(User(username="admin", password=hashed_pw))
        db.session.commit()
