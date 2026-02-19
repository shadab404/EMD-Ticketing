from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_safe_default_key') # Needed for sessions
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emdad.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


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
    return User.query.get(int(user_id))

# 3. ROUTES
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form['username']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    tickets = Ticket.query.all()
    total = len(tickets)
    open_tickets = Ticket.query.filter_by(status="Open").count()
    resolved = Ticket.query.filter(Ticket.status.in_(["Resolved","Closed"])).count()
    overdue = len([t for t in tickets if t.is_overdue()])

    return render_template("dashboard.html",
                           total=total,
                           open_tickets=open_tickets,
                           resolved=resolved,
                           overdue=overdue,
                           tickets=tickets)

if __name__ == "__main__":
    with app.app_context():
        
        db.create_all()
        
       
        admin_user = User.query.filter_by(username="admin").first()
        if not admin_user:
            print("Creating default admin user...")
            hashed_pw = bcrypt.generate_password_hash("admin123").decode('utf-8')
            new_user = User(username="admin", password=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            print("Admin created: User: admin | Pass: admin123")
        
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

