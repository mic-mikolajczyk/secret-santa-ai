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

    # Relationship to track who this participant is giving a gift to
    giving_to_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=True)
    giving_to = db.relationship('Participant', foreign_keys=[giving_to_id], remote_side=[id])

    # Wishlist items for this participant
    wishlist_items = db.relationship('WishlistItem', backref='participant', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class WishlistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(500), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Drawing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    giver_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)
    
    giver = db.relationship('Participant', foreign_keys=[giver_id])
    receiver = db.relationship('Participant', foreign_keys=[receiver_id])