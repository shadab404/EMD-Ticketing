from flask import Flask, render_template, request, redirect, url_for
from models import db, User, Ticket
from flask_login import LoginManager, login_user, login_required, logout_user
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'emdad_secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emdad.db'

db.init_app(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form['username']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect('/')
    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

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
    app.run(debug=True)
    # your existing routes above...

import os

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


