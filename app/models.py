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
    # Relationships
    stores = db.relationship('Stores', backref='province', lazy='select', primaryjoin="Province.id==Stores.province_id")

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
    # Convenience relationships (use back_populates pairs to avoid overlap warnings)
    company = db.relationship('Company', lazy='joined', primaryjoin="Stores.company_id==Company.id", back_populates='stores')
    city = db.relationship('City', lazy='joined', primaryjoin="Stores.city_id==City.id", back_populates='stores')
    market_center = db.relationship('MarketCenter', lazy='joined', primaryjoin="Stores.market_center_id==MarketCenter.id", back_populates='stores')
    # Sales relationship
    sales = db.relationship('Sales', backref='store_ref', lazy='select', primaryjoin="Stores.id==Sales.store_id")

class MarketCenter(db.Model, TimestampMixin):
    __tablename__ = 'market_centers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    # Relationships
    stores = db.relationship('Stores', back_populates='market_center', lazy='select', primaryjoin="MarketCenter.id==Stores.market_center_id")

class Company(db.Model, TimestampMixin):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    # Relationships
    stores = db.relationship('Stores', back_populates='company', lazy='select', primaryjoin="Company.id==Stores.company_id")

class City(db.Model, TimestampMixin):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    province_id = db.Column(db.Integer, db.ForeignKey('provinces.id'))
    # Relationships
    province = db.relationship('Province', backref='cities', lazy='joined', primaryjoin="City.province_id==Province.id")
    stores = db.relationship('Stores', back_populates='city', lazy='select', primaryjoin="City.id==Stores.city_id")
    market_centers = db.relationship('MarketCenter', backref='city', lazy='select', primaryjoin="City.id==MarketCenter.city_id")

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
    street = db.Column(db.String, nullable=False)
    level = db.Column(db.String, nullable=False)
    local = db.Column(db.String, nullable=False)
    status = db.Column(status_enum, default='PENDING')
    # Convenience relationships
    supervisor = db.relationship('User', lazy='joined', primaryjoin="PendingStores.supervisor_id==User.id")
    province = db.relationship('Province', lazy='joined', primaryjoin="PendingStores.province_id==Province.id")
    company = db.relationship('Company', lazy='joined', primaryjoin="PendingStores.company_id==Company.id")
    city = db.relationship('City', lazy='joined', primaryjoin="PendingStores.city_id==City.id")
    market_center = db.relationship('MarketCenter', lazy='joined', primaryjoin="PendingStores.market_center_id==MarketCenter.id")

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
    # Convenience relationships
    supervisor = db.relationship('User', lazy='joined', primaryjoin="PendingClients.supervisor_id==User.id")
    province = db.relationship('Province', lazy='joined', primaryjoin="PendingClients.province_id==Province.id")
    city = db.relationship('City', lazy='joined', primaryjoin="PendingClients.city_id==City.id")

class Sales(db.Model, TimestampMixin):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.String, db.ForeignKey('stores.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    # Relationships
    store = db.relationship('Stores', lazy='joined', primaryjoin="Sales.store_id==Stores.id")
    item = db.relationship('ItemModel', lazy='joined', primaryjoin="Sales.item_id==ItemModel.id")

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


class StoreAssignment(db.Model, TimestampMixin):
    """Assignment of salesmen/promoters to stores with approval workflow"""
    __tablename__ = 'store_assignments'
    id = db.Column(db.Integer, primary_key=True)
    
    # Staff member (polymorphic pattern)
    staff_type = db.Column(db.String, nullable=False)  # 'user' or 'pending_client'
    staff_id = db.Column(db.String, nullable=False)    # The actual ID
    
    # Store (polymorphic pattern)
    store_type = db.Column(db.String, nullable=False)  # 'store' or 'pending_store'
    store_id = db.Column(db.String, nullable=False)    # The actual ID
    
    # Role at this store
    role = db.Column(db.String, nullable=False)  # 'SALESMAN' or 'PROMOTER'
    
    # Assignment metadata
    supervisor_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    assigned_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    
    # Approval workflow
    status = db.Column(db.String, nullable=False, default='PENDING')
    # PENDING → APPROVED → ACTIVE (or REJECTED)
    approved_by = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    approved_date = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.String, nullable=True)
    
    # ERP sync tracking
    synced_to_erp = db.Column(db.Boolean, default=False)
    
    # Relationships
    supervisor = db.relationship('User', foreign_keys=[supervisor_id], backref='supervised_assignments')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_assignments')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_staff', 'staff_type', 'staff_id'),
        db.Index('idx_store', 'store_type', 'store_id'),
        db.Index('idx_role', 'role'),
        db.Index('idx_status', 'status'),
        db.Index('idx_supervisor', 'supervisor_id'),
    )


# Template generation helpers
def build_template_for_model(model_class):
    template = {}
    for column in model_class.__table__.columns:
        # Include PK only if it's a manual String key (e.g., users.id, stores.id)
        if column.primary_key:
            type_name_pk = column.type.__class__.__name__
            if type_name_pk in ("String",):
                template[column.name] = ""
            else:
                # Skip typical Integer autoincrement PKs
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