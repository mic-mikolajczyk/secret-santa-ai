from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Participant(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    has_drawn = db.Column(db.Boolean, default=False)
    avatar_url = db.Column(db.String(200))  # Added avatar URL field

    # Events created by this participant
    created_events = db.relationship('Event', backref='creator', lazy=True)

    # Events this participant is part of (many-to-many)
    events = db.relationship('Event', secondary='event_participants',
                           backref=db.backref('participants', lazy=True))

    # Wishlist items for this participant
    wishlist_items = db.relationship('WishlistItem', backref='participant', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=False)
    budget = db.Column(db.Float)  # Added budget field
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)

    # Drawings for this event
    drawings = db.relationship('Drawing', backref='event', lazy=True)

    # Event invitations
    invitations = db.relationship('EventInvitation', backref='event', lazy=True)

# Association table for Event-Participant many-to-many relationship
event_participants = db.Table('event_participants',
    db.Column('event_id', db.Integer, db.ForeignKey('event.id'), primary_key=True),
    db.Column('participant_id', db.Integer, db.ForeignKey('participant.id'), primary_key=True)
)

class EventInvitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted = db.Column(db.Boolean, default=False)

class WishlistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(500), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Drawing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    giver_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    giver = db.relationship('Participant', foreign_keys=[giver_id])
    receiver = db.relationship('Participant', foreign_keys=[receiver_id])