"""
Dashboard routes for the HONOR Supervisor Hub.

This module provides all dashboard-related functionality including:
- Main supervisor dashboard with stores, team members, and pending items
- Store and salesman creation forms
- Assignment management interface
- Admin approval interface
- Debug API endpoints

Key Features:
- Consistent SQLAlchemy ORM usage with optimized queries
- Proper authentication and authorization decorators
- Type hints and comprehensive docstrings
- Efficient data conversion and template preparation
- Professional error handling patterns

Author: HONOR Development Team
Version: 1.0.0
"""

from functools import wraps
from typing import Dict, List, Optional, Any
from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify
from sqlalchemy.orm import joinedload

from ..database import get_db_connection
from ..models import Stores, User, PendingStores, PendingClients

dashboard_bp = Blueprint('dashboard', __name__)

# Constants
ADMIN_USER_TYPE_ID = 1
PENDING_STATUS = 'PENDING'
AMBASSADOR_ROLE_KEYWORD = 'AMBASSADOR'
DEFAULT_NA_VALUE = 'N/A'


def require_auth(f):
    """Decorator to require user authentication for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def require_admin(f):
    """Decorator to require admin privileges for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        from ..extensions import db
        from ..models import User
        
        user = db.session.query(User).filter_by(id=session['user_id']).first()
        if not user or user.user_type_id != ADMIN_USER_TYPE_ID:
            return redirect(url_for('dashboard.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


def convert_stores_to_dict(stores: List[Stores]) -> List[Dict[str, Any]]:
    """Convert store objects to template-friendly dictionaries."""
    return [{
        'id': store.id,
        'store_name': store.store_name,
        'company': store.company.name if store.company else DEFAULT_NA_VALUE,
        'city_name': store.city.name if store.city else DEFAULT_NA_VALUE,
        'province_name': store.province.name if store.province else DEFAULT_NA_VALUE,
        'level': store.level,
        'local': store.local,
        'sales': store.sales
    } for store in stores]


def convert_pending_stores_to_dict(pending_stores: List[PendingStores]) -> List[Dict[str, Any]]:
    """Convert pending store objects to template-friendly dictionaries."""
    return [{
        'id': store.id,
        'store_name': store.store_name,
        'store_code': store.store_code,
        'company': store.company.name if store.company else DEFAULT_NA_VALUE,
        'city_name': store.city.name if store.city else DEFAULT_NA_VALUE,
        'province_name': store.province.name if store.province else DEFAULT_NA_VALUE,
        'market_center': store.market_center.name if store.market_center else DEFAULT_NA_VALUE,
        'level': store.level,
        'local': store.local,
        'street': store.street
    } for store in pending_stores]


def convert_pending_clients_to_dict(pending_clients: List[PendingClients]) -> List[Dict[str, Any]]:
    """Convert pending client objects to template-friendly dictionaries."""
    return [{
        'id': client.id,
        'name': client.name,
        'client_id': client.client_id,
        'gender': client.gender,
        'contact_number': client.contact_number,
        'email': client.email,
        'city_name': client.city.name if client.city else DEFAULT_NA_VALUE,
        'province_name': client.province.name if client.province else DEFAULT_NA_VALUE
    } for client in pending_clients]


def get_team_members_with_counts(supervisor_id: str) -> List[Dict[str, Any]]:
    """
    Get team members with their store counts using optimized SQLAlchemy ORM queries.
    
    Args:
        supervisor_id: The supervisor's user ID
        
    Returns:
        List of team member dictionaries with store counts included
        
    Note:
        Uses joinedload for efficient relationship loading and a single query
        for store counts to minimize database round trips.
    """
    from ..extensions import db
    from ..models import User
    
    # Get team members with their user types using joinedload for efficiency
    team_members = db.session.query(User).options(
        joinedload(User.user_type),
        joinedload(User.region_rel)
    ).filter(
        User.supervisor_id == supervisor_id
    ).all()
    
    # Convert to dict format
    team_members_data = []
    for member in team_members:
        member_dict = {
            'honor_id': member.id,
            'name': member.name,
            'position_id': member.position_id,
            'region': member.region,
            'region_name': member.region_rel.name if member.region_rel else DEFAULT_NA_VALUE,
            'phone': member.phone,
            'status': member.status,
            'user_type_name': member.user_type.name if member.user_type else DEFAULT_NA_VALUE,
            'supervisor_id': member.supervisor_id,
            'is_ambassador': AMBASSADOR_ROLE_KEYWORD in (member.user_type.name or '').upper(),
            'store_count': 0  # Will be updated below
        }
        team_members_data.append(member_dict)
    
    # Get store counts for each team member in a single optimized query
    if team_members_data:
        member_ids = [str(member['honor_id']) for member in team_members_data]
        
        # Single query to get all store counts at once
        store_counts = db.session.query(
            Stores.supervisor_id,
            db.func.count(Stores.id).label('store_count')
        ).filter(
            Stores.supervisor_id.in_(member_ids)
        ).group_by(Stores.supervisor_id).all()
        
        # Create lookup dictionary for O(1) access
        store_counts_dict = {str(count.supervisor_id): count.store_count for count in store_counts}
        
        # Update team members with store counts
        for member in team_members_data:
            member['store_count'] = int(store_counts_dict.get(str(member['honor_id']), 0))
    
    return team_members_data


@dashboard_bp.route('/dashboard')
@require_auth
def dashboard() -> str:
    """
    Main dashboard route displaying supervisor's stores, team members, and pending items.
    
    Returns:
        Rendered dashboard template with all relevant data for the supervisor.
    """
    from ..extensions import db
    from ..models import User
    
    supervisor_id = session['user_id']
    
    # Get current user to check if admin
    current_user = db.session.query(User).filter_by(id=supervisor_id).first()
    is_admin = current_user and current_user.user_type_id == ADMIN_USER_TYPE_ID
    
    # Load stores with relationships using SQLAlchemy ORM with joinedload for efficiency
    stores = db.session.query(Stores).options(
        joinedload(Stores.sales),
        joinedload(Stores.company),
        joinedload(Stores.city),
        joinedload(Stores.province),
        joinedload(Stores.market_center)
    ).filter(
        Stores.supervisor_id == supervisor_id
    ).all()

    # Load pending stores with relationships
    pending_stores = db.session.query(PendingStores).options(
        joinedload(PendingStores.company),
        joinedload(PendingStores.city),
        joinedload(PendingStores.province),
        joinedload(PendingStores.market_center)
    ).filter(
        PendingStores.supervisor_id == supervisor_id,
        PendingStores.status == PENDING_STATUS
    ).all()

    # Load pending clients with relationships
    pending_clients = db.session.query(PendingClients).options(
        joinedload(PendingClients.city),
        joinedload(PendingClients.province)
    ).filter(
        PendingClients.supervisor_id == supervisor_id,
        PendingClients.status == PENDING_STATUS
    ).all()

    # Convert data to template-friendly format
    stores_data = convert_stores_to_dict(stores)
    pending_stores_data = convert_pending_stores_to_dict(pending_stores)
    pending_clients_data = convert_pending_clients_to_dict(pending_clients)
    
    # Get team members with store counts
    team_members = get_team_members_with_counts(supervisor_id)
    
    # Calculate promoters count
    promoters_count = sum(1 for member in team_members if member.get('is_ambassador'))

    return render_template(
        'dashboard.html',
        stores=stores_data,
        team_members=team_members,
        promoters_count=promoters_count,
        pending_stores=pending_stores_data,
        pending_clients=pending_clients_data,
        is_admin=is_admin
    )


@dashboard_bp.route('/api/dashboard-debug')
@require_auth
def dashboard_debug() -> Dict[str, Any]:
    """
    Debug API endpoint providing dashboard metrics and sample data.
    
    Returns:
        JSON response with counts, samples, and debug information.
    """
    from ..extensions import db
    from ..models import User
    
    supervisor_id = session['user_id']
    
    # Get counts using SQLAlchemy ORM for consistency
    stores_count = db.session.query(Stores).filter(
        Stores.supervisor_id == supervisor_id
    ).count()
    
    pending_stores_count = db.session.query(PendingStores).filter(
        PendingStores.supervisor_id == supervisor_id,
        PendingStores.status == PENDING_STATUS
    ).count()
    
    pending_clients_count = db.session.query(PendingClients).filter(
        PendingClients.supervisor_id == supervisor_id,
        PendingClients.status == PENDING_STATUS
    ).count()
    
    # Get team members sample
    team_members = db.session.query(User).options(
        joinedload(User.user_type)
    ).filter(
        User.supervisor_id == supervisor_id
    ).limit(50).all()
    
    team_members_list = [{
        'honor_id': member.id,
        'name': member.name,
        'user_type_id': member.user_type_id,
        'supervisor_id': member.supervisor_id,
        'user_type_name': member.user_type.name if member.user_type else DEFAULT_NA_VALUE
    } for member in team_members]
    
    # Get any users sample for debugging
    any_users = db.session.query(User).limit(50).all()
    any_users_list = [{
        'id': user.id,
        'name': user.name,
        'user_type_id': user.user_type_id,
        'supervisor_id': user.supervisor_id
    } for user in any_users]
    
    promoters_count = sum(1 for m in team_members_list if AMBASSADOR_ROLE_KEYWORD in (m.get('user_type_name') or '').upper())

    return jsonify({
        'session_user_id': session.get('user_id'),
        'stores_count': stores_count,
        'team_members_count': len(team_members_list),
        'promoters_count': promoters_count,
        'pending_stores_count': pending_stores_count,
        'pending_clients_count': pending_clients_count,
        'team_members_sample': team_members_list[:3],
        'users_any_sample': any_users_list,
    })

@dashboard_bp.route('/create-store')
@require_auth
def create_store_page() -> str:
    """
    Store creation form page with dropdown options.
    
    Returns:
        Rendered store creation template with all required options.
    """
    from ..extensions import db
    from ..models import Province, City, Company, MarketCenter
    
    # Get all provinces
    provinces = db.session.query(Province).order_by(Province.name).all()
    
    # Get all cities grouped by province
    cities = db.session.query(City).join(Province).order_by(Province.name, City.name).all()
    
    # Get all companies
    companies = db.session.query(Company).order_by(Company.name).all()
    
    # Get all market centers
    market_centers = db.session.query(MarketCenter).order_by(MarketCenter.name).all()
    
    return render_template('create_store.html',
                         provinces=provinces,
                         cities=cities,
                         companies=companies,
                         market_centers=market_centers)


@dashboard_bp.route('/create-salesman')
@require_auth
def create_salesman_page() -> str:
    """
    Salesman creation form page with location options.
    
    Returns:
        Rendered salesman creation template with province and city options.
    """
    from ..extensions import db
    from ..models import Province, City
    
    # Get all provinces
    provinces = db.session.query(Province).order_by(Province.name).all()
    
    # Get all cities grouped by province
    cities = db.session.query(City).join(Province).order_by(Province.name, City.name).all()
    
    return render_template('create_salesman.html',
                         provinces=provinces,
                         cities=cities)


@dashboard_bp.route('/assignments')
@require_auth
def assignments_page() -> str:
    """
    Assignment manager page with dual-list UI for managing store assignments.
    
    Returns:
        Rendered assignments template with active and pending stores.
    """
    from ..extensions import db
    from ..models import Stores, PendingStores
    
    supervisor_id = session['user_id']
    
    # Get all stores (active and pending) for the supervisor
    active_stores = db.session.query(Stores).options(
        joinedload(Stores.company),
        joinedload(Stores.city),
        joinedload(Stores.province)
    ).filter(
        Stores.supervisor_id == supervisor_id
    ).all()
    
    pending_stores = db.session.query(PendingStores).options(
        joinedload(PendingStores.company),
        joinedload(PendingStores.city),
        joinedload(PendingStores.province)
    ).filter(
        PendingStores.supervisor_id == supervisor_id,
        PendingStores.status == PENDING_STATUS
    ).all()
    
    return render_template('assignments.html',
                         active_stores=active_stores,
                         pending_stores=pending_stores)


@dashboard_bp.route('/admin/approvals')
@require_admin
def admin_approvals_page() -> str:
    """
    Admin interface for approving pending assignments.
    
    Returns:
        Rendered admin approvals template for managing pending items.
    """
    return render_template('admin_approvals.html')


