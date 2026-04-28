"""
database.py - SQLite database models using Flask-SQLAlchemy
Tables: Patients, Visits, Payments
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'Nurse' or 'Doctor'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }

class Patient(db.Model):
    __tablename__ = 'patients'

    patient_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    dob = db.Column(db.String(20), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    visits = db.relationship('Visit', backref='patient', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='patient', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'patient_id': self.patient_id,
            'name': self.name,
            'phone': self.phone,
            'dob': self.dob,
            'age': self.age,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }


class Visit(db.Model):
    __tablename__ = 'visits'

    visit_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    symptoms = db.Column(db.Text, nullable=True)
    duration = db.Column(db.String(100), nullable=True)
    medical_history = db.Column(db.Text, nullable=True)
    transcript = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    visit_hash = db.Column(db.String(64), nullable=True)  # SHA-256 hash

    # Relationship
    payment = db.relationship('Payment', backref='visit', lazy=True, uselist=False)

    def to_dict(self):
        return {
            'visit_id': self.visit_id,
            'patient_id': self.patient_id,
            'date': self.date.strftime('%Y-%m-%d %H:%M') if self.date else '',
            'symptoms': self.symptoms,
            'duration': self.duration,
            'medical_history': self.medical_history,
            'visit_hash': self.visit_hash
        }


class Payment(db.Model):
    __tablename__ = 'payments'

    payment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'), nullable=False)
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.visit_id'), nullable=False)
    status = db.Column(db.String(20), default='Not Paid')   # 'Paid' or 'Not Paid'
    amount = db.Column(db.Float, default=500.0)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'payment_id': self.payment_id,
            'patient_id': self.patient_id,
            'visit_id': self.visit_id,
            'status': self.status,
            'amount': self.amount,
            'date': self.date.strftime('%Y-%m-%d %H:%M') if self.date else ''
        }


def init_db(app):
    """Initialize the database with the Flask app."""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("[OK] Database initialized successfully.")
