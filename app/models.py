from datetime import datetime
from .extensions import db

# Enum for status
status_enum = db.Enum("ACTIVE", "PENDING", "INACTIVE", name="status_enum")

# Timestamp mixin
class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(db.Model, TimestampMixin):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    position_id = db.Column(db.String)
    user_type_id = db.Column(db.Integer, db.ForeignKey('user_types.id'), nullable=False)
    supervisor_id = db.Column(db.String, db.ForeignKey('users.id'))
    region = db.Column(db.Integer, db.ForeignKey('regions.id'))
    phone = db.Column(db.String)
    entry_date = db.Column(db.Date)
    exit_date = db.Column(db.Date)
    status = db.Column(status_enum, default='ACTIVE')
    password_hash = db.Column(db.String, nullable=False)
    is_first_login = db.Column(db.Boolean, default=True)

class UserType(db.Model, TimestampMixin):
    __tablename__ = 'user_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

class Province(db.Model, TimestampMixin):
    __tablename__ = 'provinces'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    rm_id = db.Column(db.Integer, nullable=False)

class Stores(db.Model, TimestampMixin):
    __tablename__ = 'stores'
    id = db.Column(db.String, primary_key=True) # Store Code
    store_name = db.Column(db.String, nullable=False)
    province_id = db.Column(db.Integer, db.ForeignKey('provinces.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    market_center_id = db.Column(db.Integer, db.ForeignKey('market_centers.id'), nullable=False)
    supervisor_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(status_enum, default='ACTIVE')
    street = db.Column(db.String, nullable=False)
    level = db.Column(db.String, nullable=False)
    local = db.Column(db.String, nullable=False)

    supervisor = db.relationship('User', backref='stores', foreign_keys=[supervisor_id])

class MarketCenter(db.Model, TimestampMixin):
    __tablename__ = 'market_centers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)

class Company(db.Model, TimestampMixin):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

class City(db.Model, TimestampMixin):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

class PendingStores(db.Model, TimestampMixin):
    __tablename__ = 'pending_stores'
    id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String, nullable=False)
    store_code = db.Column(db.String, nullable=False)
    province_id = db.Column(db.Integer, db.ForeignKey('provinces.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    market_center_id = db.Column(db.Integer, db.ForeignKey('market_centers.id'), nullable=False)
    supervisor_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(status_enum, default='PENDING')

class PendingClients(db.Model, TimestampMixin):
    __tablename__ = 'pending_clients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    client_id = db.Column(db.String, nullable=False)
    gender = db.Column(db.String, nullable=False)
    contact_number = db.Column(db.String, nullable=False)
    email = db.Column(db.String)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    province_id = db.Column(db.Integer, db.ForeignKey('provinces.id'), nullable=False)
    supervisor_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(status_enum, default='PENDING')

class Sales(db.Model, TimestampMixin):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.String, db.ForeignKey('stores.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)

class ItemModel(db.Model, TimestampMixin):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    code = db.Column(db.String, nullable=False)

class Region(db.Model, TimestampMixin):
    __tablename__ = 'regions'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String, nullable=False)


# Template generation helpers
def build_template_for_model(model_class):
    template = {}
    for column in model_class.__table__.columns:
        if column.primary_key:
            continue
        if column.name in ("created_at", "updated_at"):
            continue
        # Provide simple defaults/placeholders
        type_name = column.type.__class__.__name__
        if type_name in ("String", "Enum"):
            template[column.name] = ""
        elif type_name in ("Integer", "Float"):
            template[column.name] = 0
        elif type_name in ("Date", "DateTime"):
            template[column.name] = None
        else:
            template[column.name] = None
    return template


def iter_mapped_models():
    # Yield all mapped model classes registered with SQLAlchemy
    for mapper in db.Model.registry.mappers:
        model_cls = mapper.class_
        # Ensure it has a __tablename__ (skip abstract/mixins)
        if getattr(model_cls, '__tablename__', None):
            yield model_cls


def get_tablename_to_model():
    return {m.__tablename__: m for m in iter_mapped_models()}


def generate_general_template():
    # Dynamically build templates for all mapped models
    templates = {}
    for model_cls in iter_mapped_models():
        templates[model_cls.__tablename__] = build_template_for_model(model_cls)
    return templates