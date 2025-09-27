from datetime import datetime
from .extensions import db


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
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

class Province(db.Model):
    __tablename__ = 'regions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    rm_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Stores(db.Model):
    __tablename__ = 'stores'
    id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String, nullable=False)
    store_code = db.Column(db.String, nullable=False)
    province_id = db.Column(db.Integer, nullable=False)
    company_id = db.Column(db.Integer, nullable=False)
    city_id = db.Column(db.Integer, nullable=False)
    market_center_id = db.Column(db.Integer, nullable=False)
    supervisor_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String, default='ACTIVE')
    street = db.Column(db.String, nullable=False)
    level = db.Column(db.String, nullable=False)
    local = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class MarketCenter(db.Model):
    __tablename__ = 'market_centers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class City(db.Model):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PendingStores(db.Model):
    __tablename__ = 'pending_stores'
    id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String, nullable=False)
    store_code = db.Column(db.String, nullable=False)
    province_id = db.Column(db.Integer, nullable=False)
    company_id = db.Column(db.Integer, nullable=False)
    city_id = db.Column(db.Integer, nullable=False)
    market_center_id = db.Column(db.Integer, nullable=False)
    supervisor_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String, default='PENDING')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Sales(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    sales = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class itemModel(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    code = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)