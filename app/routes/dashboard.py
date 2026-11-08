"""Dashboard routes for Supervisor Hub."""

import csv
import io
from datetime import datetime
from functools import wraps
from typing import Dict, List, Any
from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify, make_response, flash
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models import Stores, User, PendingStores, PendingClients, StoreAssignment, Sales, Region

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
            'employee_id': member.id,
            'name': member.name,
            'position_id': member.position_id,
            'region': member.region_id,
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
        member_ids = [str(member['employee_id']) for member in team_members_data]
        
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
            member['store_count'] = int(store_counts_dict.get(str(member['employee_id']), 0))
    
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

    # Operational indicators
    pending_assignments = db.session.query(StoreAssignment).filter(
        StoreAssignment.supervisor_id == supervisor_id,
        StoreAssignment.status == 'PENDING'
    ).count()

    approved_not_synced = db.session.query(StoreAssignment).filter(
        StoreAssignment.supervisor_id == supervisor_id,
        StoreAssignment.status == 'APPROVED',
        StoreAssignment.synced_to_erp == False
    ).count()

    now = datetime.utcnow()
    total_sales_this_month = db.session.query(
        db.func.coalesce(db.func.sum(Sales.quantity), 0)
    ).join(Stores, Sales.store_id == Stores.id).filter(
        Stores.supervisor_id == supervisor_id,
        Sales.month == now.month,
        Sales.year == now.year
    ).scalar()

    # Staff by region breakdown
    staff_by_region = db.session.query(
        Region.name,
        db.func.count(User.id)
    ).join(User, User.region_id == Region.id).filter(
        User.supervisor_id == supervisor_id,
        User.status == 'ACTIVE'
    ).group_by(Region.name).all()

    return render_template(
        'dashboard.html',
        stores=stores_data,
        team_members=team_members,
        promoters_count=promoters_count,
        pending_stores=pending_stores_data,
        pending_clients=pending_clients_data,
        is_admin=is_admin,
        pending_assignments=pending_assignments,
        approved_not_synced=approved_not_synced,
        total_sales_this_month=total_sales_this_month,
        staff_by_region=staff_by_region,
        current_month=now.month,
        current_year=now.year,
    )



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
    return render_template('admin_approvals.html')


def _csv_safe(v):
    """Prevent CSV formula injection when opened in Excel."""
    s = '' if v is None else str(v)
    return "'" + s if s[:1] in ('=', '+', '-', '@', '\t', '\r') else s


@dashboard_bp.route('/erp/export')
@require_auth
def erp_export():
    """Download approved assignments as CSV for ERP upload."""
    supervisor_id = session['user_id']

    assignments = db.session.query(StoreAssignment).filter(
        StoreAssignment.supervisor_id == supervisor_id,
        StoreAssignment.status == 'APPROVED',
        StoreAssignment.synced_to_erp == False
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'assignment_id', 'staff_type', 'staff_id', 'staff_name',
        'store_type', 'store_id', 'store_name', 'role',
        'assigned_date', 'approved_date'
    ])

    for a in assignments:
        staff_name = ''
        if a.staff_type == 'user':
            staff = db.session.query(User).filter_by(id=a.staff_id).first()
            staff_name = staff.name if staff else ''
        else:
            from ..models import PendingClients as PC
            client = db.session.query(PC).filter_by(id=int(a.staff_id)).first()
            staff_name = client.name if client else ''

        store_name = ''
        if a.store_type == 'store':
            store = db.session.query(Stores).filter_by(id=a.store_id).first()
            store_name = store.store_name if store else ''
        else:
            ps = db.session.query(PendingStores).filter_by(id=int(a.store_id)).first()
            store_name = ps.store_name if ps else ''

        writer.writerow([
            a.id, a.staff_type, a.staff_id, _csv_safe(staff_name),
            a.store_type, a.store_id, _csv_safe(store_name), a.role,
            a.assigned_date.strftime('%Y-%m-%d') if a.assigned_date else '',
            a.approved_date.strftime('%Y-%m-%d') if a.approved_date else '',
        ])

    resp = make_response(output.getvalue())
    resp.headers['Content-Type'] = 'text/csv; charset=utf-8'
    resp.headers['Content-Disposition'] = f'attachment; filename=erp_export_{datetime.utcnow().strftime("%Y%m%d")}.csv'
    return resp


@dashboard_bp.route('/erp/import', methods=['POST'])
@require_auth
def erp_import():
    """Upload ERP response CSV to mark assignments as synced."""
    if 'file' not in request.files:
        flash('No se seleccionó ningún archivo', 'error')
        return redirect(url_for('dashboard.dashboard'))

    file = request.files['file']
    if not file.filename or not file.filename.endswith('.csv'):
        flash('El archivo debe ser CSV', 'error')
        return redirect(url_for('dashboard.dashboard'))

    try:
        stream = io.StringIO(file.stream.read().decode('utf-8'))
        reader = csv.DictReader(stream)

        synced_ids = []
        for row in reader:
            aid = row.get('assignment_id', '').strip()
            if aid and aid.isdigit():
                synced_ids.append(int(aid))

        if synced_ids:
            db.session.query(StoreAssignment).filter(
                StoreAssignment.id.in_(synced_ids),
                StoreAssignment.status == 'APPROVED',
                StoreAssignment.supervisor_id == session['user_id']
            ).update({'synced_to_erp': True}, synchronize_session=False)
            db.session.commit()

        flash(f'{len(synced_ids)} asignaciones marcadas como sincronizadas con ERP', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error procesando archivo: {str(e)}', 'error')

    return redirect(url_for('dashboard.dashboard'))


