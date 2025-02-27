import os
import random
from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///santa.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import models after db initialization
from models import Participant, WishlistItem

@login_manager.user_loader
def load_user(id):
    return Participant.query.get(int(id))

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if not name or not email or not password:
            flash("Please fill in all fields!", "danger")
            return redirect(url_for("register"))

        if Participant.query.filter_by(email=email).first():
            flash("Email already registered!", "warning")
            return redirect(url_for("register"))

        participant = Participant(name=name, email=email)
        participant.set_password(password)
        db.session.add(participant)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        participant = Participant.query.filter_by(email=email).first()

        if participant and participant.check_password(password):
            login_user(participant)
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password", "danger")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/draw")
@login_required
def draw():
    if current_user.has_drawn:
        flash("You have already drawn a name!", "warning")
        return redirect(url_for("dashboard"))

    # Get all participants except current user who haven't been drawn
    available = Participant.query.filter(
        Participant.id != current_user.id,
        ~Participant.id.in_(
            db.session.query(Participant.giving_to_id).filter(Participant.giving_to_id != None)
        )
    ).all()

    if not available:
        flash("No available participants to draw!", "warning")
        return redirect(url_for("dashboard"))

    drawn = random.choice(available)
    current_user.giving_to = drawn
    current_user.has_drawn = True
    db.session.commit()

    flash(f"You will be giving a gift to {drawn.name}!", "success")
    return redirect(url_for("dashboard"))

@app.route("/wishlist", methods=["GET", "POST"])
@login_required
def wishlist():
    if request.method == "POST":
        description = request.form.get("description")
        if description:
            item = WishlistItem(description=description, participant=current_user)
            db.session.add(item)
            db.session.commit()
            flash("Wishlist item added!", "success")
        return redirect(url_for("wishlist"))

    return render_template("wishlist.html")

@app.route("/wishlist/<int:participant_id>")
@login_required
def view_wishlist(participant_id):
    participant = Participant.query.get_or_404(participant_id)
    return render_template("view_wishlist.html", participant=participant)

# Create tables
with app.app_context():
    db.create_all()