import os
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Ticket
from datetime import datetime, timedelta

app = Flask(__name__)

# Fix for Render proxy (IMPORTANT)
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Force HTTPS scheme
app.config['PREFERRED_URL_SCHEME'] = 'https'

# Secret key from environment variable
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "super-secret-key-123")

# PostgreSQL for Render
database_url = os.getenv("DATABASE_URL")

if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
else:
    database_url = "sqlite:///tickets.db"

app.config['SQLALCHEMY_DATABASE_URI'] = database_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Email Config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_app_password'

db.init_app(app)
mail = Mail(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# with app.app_context():
#     db.create_all()
# ---------------- AUTH ---------------- #

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid email or password")

    return render_template("login.html")

# ---------------- DASHBOARD ---------------- #

@app.route("/dashboard")
@login_required
def dashboard():
    tickets = Ticket.query.all()
    open_count = Ticket.query.filter_by(status="Open").count()
    closed_count = Ticket.query.filter_by(status="Closed").count()
    return render_template("dashboard.html",
                           tickets=tickets,
                           open_count=open_count,
                           closed_count=closed_count)

# ---------------- CREATE TICKET ---------------- #

@app.route("/create", methods=["GET", "POST"])
@login_required
def create_ticket():
    if request.method == "POST":

        file = request.files.get("attachment")
        filename = None
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        ticket = Ticket(
            title=request.form["title"],
            description=request.form["description"],
            priority=request.form["priority"],
            created_by=current_user.id,
            sla_deadline=datetime.utcnow() + timedelta(days=2),
            attachment=filename
        )
        db.session.add(ticket)
        db.session.commit()

        # Send Email
        try:
            msg = Message(
                subject="New Ticket Created",
                sender=app.config['MAIL_USERNAME'],
                recipients=[current_user.email]
            )
            msg.body = f"Ticket '{ticket.title}' created successfully."
            mail.send(msg)
        except:
            pass

        return redirect(url_for("dashboard"))

    return render_template("create_ticket.html")

# ---------------- ADMIN PANEL ---------------- #

@app.route("/admin")
@login_required
def admin_panel():
    if current_user.role != "admin":
        return "Access Denied"

    users = User.query.all()
    tickets = Ticket.query.all()
    return render_template("admin.html", users=users, tickets=tickets)

# ---------------- FILE DOWNLOAD ---------------- #

@app.route("/uploads/<filename>")
@login_required
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port) 

@app.route("/create-admin")
def create_admin():
    from werkzeug.security import generate_password_hash

    if User.query.filter_by(email="admin@gmail.com").first():
        return "Admin already exists"

    admin = User(
        username="admin",
        email="admin@gmail.com",
        password=generate_password_hash("admin123"),
        role="admin"
    )

    db.session.add(admin)
    db.session.commit()

    return "Admin created successfully!"
