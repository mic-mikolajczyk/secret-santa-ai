from app import db

class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

class Drawing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    giver_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)
    
    giver = db.relationship('Participant', foreign_keys=[giver_id])
    receiver = db.relationship('Participant', foreign_keys=[receiver_id])
