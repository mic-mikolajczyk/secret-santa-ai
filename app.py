from src.models import Participant, WishlistItem, Drawing, Event, EventInvitation
import os
import random
import hashlib
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user


from database import db

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


def get_gravatar_url(email, size=100):
    """Generate Gravatar URL for a given email"""
    email_hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
    return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d=identicon"


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
        participant.avatar_url = get_gravatar_url(email)  # Set avatar URL
        db.session.add(participant)
        db.session.commit()

        # Check for pending invitations
        invitations = EventInvitation.query.filter_by(
            email=email, accepted=False).all()
        for invitation in invitations:
            event = Event.query.get(invitation.event_id)
            if event:
                event.participants.append(participant)
                invitation.accepted = True
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
    public_events = Event.query.filter_by(is_public=True).all()
    return render_template("dashboard.html", public_events=public_events)


@app.route("/create_event", methods=["GET", "POST"])
@login_required
def create_event():
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        budget = request.form.get("budget", type=float)
        is_public = request.form.get("is_public") == "on"

        if not name:
            flash("Please provide an event name!", "danger")
            return redirect(url_for("create_event"))

        event = Event(
            name=name,
            description=description,
            budget=budget,
            is_public=is_public,
            creator=current_user
        )
        event.participants.append(current_user)  # Add creator as participant
        db.session.add(event)
        db.session.commit()

        flash("Event created successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("create_event.html")


@app.route("/event/<int:event_id>/invite", methods=["GET", "POST"])
@login_required
def invite_participants(event_id):
    event = Event.query.get_or_404(event_id)
    if event.creator_id != current_user.id:
        flash("Only the event creator can send invitations!", "danger")
        return redirect(url_for("event_dashboard", event_id=event_id))

    if request.method == "POST":
        emails = request.form.get("emails", "").split()
        for email in emails:
            email = email.strip()
            if email:
                # Check if user already exists
                participant = Participant.query.filter_by(email=email).first()
                if participant:
                    if participant not in event.participants:
                        event.participants.append(participant)
                        flash(f"{email} has been added to the event!", "success")
                else:
                    # Create invitation
                    invitation = EventInvitation(event=event, email=email)
                    db.session.add(invitation)
                    flash(f"Invitation sent to {email}!", "success")

        db.session.commit()
        return redirect(url_for("invite_participants", event_id=event_id))

    return render_template("invite_participants.html", event=event)


@app.route("/event/<int:event_id>/join", methods=["POST"])
@login_required
def join_event(event_id):
    event = Event.query.get_or_404(event_id)
    if not event.is_public:
        flash("This event is private!", "danger")
        return redirect(url_for("dashboard"))

    if current_user in event.participants:
        flash("You are already a participant in this event!", "warning")
    else:
        event.participants.append(current_user)
        db.session.commit()
        flash("You have joined the event successfully!", "success")

    return redirect(url_for("dashboard"))


@app.route("/event/<int:event_id>")
@login_required
def event_dashboard(event_id):
    event = Event.query.get_or_404(event_id)
    if current_user not in event.participants:
        flash("You are not a participant in this event!", "danger")
        return redirect(url_for("dashboard"))

    drawing = Drawing.query.filter_by(
        event_id=event.id, giver_id=current_user.id).first()
    wishlist_items = WishlistItem.query.filter_by(
        event_id=event.id,
        participant_id=current_user.id
    ).order_by(WishlistItem.created_at.desc()).all()

    return render_template("event_dashboard.html",
                           event=event,
                           drawing=drawing,
                           wishlist_items=wishlist_items)


@app.route("/event/<int:event_id>/draw")
@login_required
def draw(event_id):
    event = Event.query.get_or_404(event_id)
    if current_user not in event.participants:
        flash("You are not a participant in this event!", "danger")
        return redirect(url_for("dashboard"))

    if Drawing.query.filter_by(event_id=event.id, giver_id=current_user.id).first():
        flash("You have already drawn a name!", "warning")
        return redirect(url_for("event_dashboard", event_id=event.id))

    # Get all participants except current user who haven't been drawn in this event
    available = [p for p in event.participants
                 if p != current_user and
                 not Drawing.query.filter_by(event_id=event.id, receiver_id=p.id).first()]

    if not available:
        flash("No available participants to draw!", "warning")
        return redirect(url_for("event_dashboard", event_id=event.id))

    drawn = random.choice(available)
    drawing = Drawing(event_id=event.id, giver=current_user, receiver=drawn)
    db.session.add(drawing)

    # Update the has_drawn attribute
    current_user.has_drawn = True

    db.session.commit()

    flash(f"You will be giving a gift to {drawn.name}!", "success")
    return redirect(url_for("event_dashboard", event_id=event.id))


@app.route("/event/<int:event_id>/wishlist", methods=["POST"])
@login_required
def add_wishlist_item(event_id):
    event = Event.query.get_or_404(event_id)
    if current_user not in event.participants:
        flash("You are not a participant in this event!", "danger")
        return redirect(url_for("dashboard"))

    description = request.form.get("description")
    if description:
        item = WishlistItem(
            description=description,
            participant=current_user,
            event_id=event_id
        )
        db.session.add(item)
        db.session.commit()
        flash("Wishlist item added!", "success")

    return redirect(url_for("event_dashboard", event_id=event_id))


@app.route("/event/<int:event_id>/wishlist/<int:participant_id>")
@login_required
def view_wishlist(event_id, participant_id):
    event = Event.query.get_or_404(event_id)
    participant = Participant.query.get_or_404(participant_id)
    if current_user not in event.participants:
        flash("You are not a participant in this event!", "danger")
        return redirect(url_for("dashboard"))

    drawing = Drawing.query.filter_by(
        event_id=event.id,
        giver_id=current_user.id,
        receiver_id=participant_id
    ).first()

    if not drawing:
        flash("You can only view the wishlist of the person you're giving a gift to!", "danger")
        return redirect(url_for("event_dashboard", event_id=event_id))

    wishlist_items = WishlistItem.query.filter_by(
        event_id=event.id,
        participant_id=participant_id
    ).order_by(WishlistItem.created_at.desc()).all()

    return render_template("view_wishlist.html",
                           event=event,
                           participant=participant,
                           wishlist_items=wishlist_items)


@app.route("/event/<int:event_id>/wishlist/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_wishlist_item(event_id, item_id):
    item = WishlistItem.query.get_or_404(item_id)
    if current_user != item.participant:
        flash("You can only delete your own wishlist items!", "danger")
        return redirect(url_for("event_dashboard", event_id=event_id))

    db.session.delete(item)
    db.session.commit()
    flash("Wishlist item deleted!", "success")
    return redirect(url_for("event_dashboard", event_id=event_id))


@app.route("/event/<int:event_id>/delete", methods=["POST"])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.creator_id != current_user.id:
        flash("You can only delete events you created!", "danger")
        return redirect(url_for("dashboard"))

    db.session.delete(event)
    db.session.commit()
    flash("Event deleted successfully!", "success")
    return redirect(url_for("dashboard"))


# Drop all tables and recreate them
with app.app_context():
    db.drop_all()
    db.create_all()
