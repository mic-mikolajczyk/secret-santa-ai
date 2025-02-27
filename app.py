import os
import random
from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///santa.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Import models after db initialization
from models import Participant, Drawing

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        
        if not name or not email:
            flash("Please fill in all fields!", "danger")
            return redirect(url_for("index"))
        
        # Check for duplicate email
        if Participant.query.filter_by(email=email).first():
            flash("This email is already registered!", "warning")
            return redirect(url_for("index"))
        
        participant = Participant(name=name, email=email)
        db.session.add(participant)
        db.session.commit()
        flash("Participant added successfully!", "success")
        return redirect(url_for("index"))
    
    participants = Participant.query.all()
    drawings = Drawing.query.all()
    return render_template("index.html", participants=participants, drawings=drawings)

@app.route("/draw", methods=["POST"])
def draw_names():
    participants = Participant.query.all()
    if len(participants) < 2:
        flash("Need at least 2 participants for drawing!", "warning")
        return redirect(url_for("index"))
    
    # Clear previous drawings
    Drawing.query.delete()
    db.session.commit()
    
    # Create list of givers and receivers
    givers = participants.copy()
    receivers = participants.copy()
    
    # Shuffle and assign
    drawings = []
    for giver in givers:
        possible_receivers = [r for r in receivers if r != giver]
        if not possible_receivers:
            # Reset if we get stuck
            return draw_names()
        
        receiver = random.choice(possible_receivers)
        receivers.remove(receiver)
        drawings.append(Drawing(giver_id=giver.id, receiver_id=receiver.id))
    
    db.session.bulk_save_objects(drawings)
    db.session.commit()
    flash("Names have been drawn!", "success")
    return redirect(url_for("index"))

@app.route("/reset", methods=["POST"])
def reset():
    Drawing.query.delete()
    Participant.query.delete()
    db.session.commit()
    flash("Everything has been reset!", "info")
    return redirect(url_for("index"))

# Create tables
with app.app_context():
    db.create_all()
