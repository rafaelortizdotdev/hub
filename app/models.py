from datetime import datetime
from .extensions import db


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    honor_id = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    position_id = db.Column(db.String)
    user_type_id = db.Column(db.Integer, nullable=False)
    supervisor_id = db.Column(db.Integer)
    region = db.Column(db.String)
    rm = db.Column(db.String)
    phone = db.Column(db.String)
    entry_date = db.Column(db.Date)
    exit_date = db.Column(db.Date)
    status = db.Column(db.String, default='ACTIVE')
    password_hash = db.Column(db.String, nullable=False, default='honor1##')
    is_first_login = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserType(db.Model):
    __tablename__ = 'user_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Region(db.Model):
    __tablename__ = 'regions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    rm_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
