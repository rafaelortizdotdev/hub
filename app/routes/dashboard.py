from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify
from sqlalchemy.orm import joinedload

from ..database import get_db_connection
from ..models import Stores, User, PendingStores, PendingClients

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    from ..extensions import db
    from ..models import User
    
    # Get current user to check if admin
    current_user = db.session.query(User).filter_by(id=session['user_id']).first()
    is_admin = current_user and current_user.user_type_id == 1  # Assuming 1 is admin
    
    # Use SQLAlchemy ORM to load stores with relationships
    stores = db.session.query(Stores).options(
        joinedload(Stores.sales),
        joinedload(Stores.company),
        joinedload(Stores.city),
        joinedload(Stores.province),
        joinedload(Stores.market_center)
    ).filter(
        Stores.supervisor_id == session['user_id']
    ).all()

    conn = get_db_connection()

    team_members_rows = conn.execute(
        '''
        SELECT 
            u.id AS honor_id,
            u.name,
            u.position_id,
            u.region,
            r.name AS region_name,
            u.phone,
            u.status,
            ut.name AS user_type_name,
            u.supervisor_id AS supervisor_id
        FROM users u 
        JOIN user_types ut ON u.user_type_id = ut.id 
        LEFT JOIN regions r ON CAST(u.region AS INTEGER) = r.id
        WHERE (
            CAST(u.supervisor_id AS TEXT) = ?
            OR UPPER(CAST(u.supervisor_id AS TEXT)) = UPPER(?)
            OR LOWER(CAST(u.supervisor_id AS TEXT)) = LOWER(?)
        )
        ''',
        (session['user_id'], session['user_id'], session['user_id']),
    ).fetchall()

    # Use SQLAlchemy ORM to load pending stores with relationships
    pending_stores = db.session.query(PendingStores).options(
        joinedload(PendingStores.company),
        joinedload(PendingStores.city),
        joinedload(PendingStores.province),
        joinedload(PendingStores.market_center)
    ).filter(
        PendingStores.supervisor_id == session['user_id'],
        PendingStores.status == 'PENDING'
    ).all()

    # Use SQLAlchemy ORM to load pending clients with relationships
    pending_clients = db.session.query(PendingClients).options(
        joinedload(PendingClients.city),
        joinedload(PendingClients.province)
    ).filter(
        PendingClients.supervisor_id == session['user_id'],
        PendingClients.status == 'PENDING'
    ).all()

    # Convert stores to dict format for template compatibility
    stores_data = []
    for store in stores:
        store_dict = {
            'id': store.id,
            'store_name': store.store_name,
            'company': store.company.name if store.company else 'N/A',
            'city_name': store.city.name if store.city else 'N/A',
            'province_name': store.province.name if store.province else 'N/A',
            'level': store.level,
            'local': store.local,
            'sales': store.sales  # Include sales relationship
        }
        stores_data.append(store_dict)

    team_members = [dict(r) for r in team_members_rows]

    member_ids = [str(m.get('honor_id')) for m in team_members if m.get('honor_id') is not None]
    store_counts_by_supervisor = {}
    if member_ids:
        placeholders = ','.join(['?'] * len(member_ids))
        count_rows = conn.execute(
            f"""
            SELECT CAST(supervisor_id AS TEXT) AS supervisor_id_text, COUNT(1) AS c
            FROM stores
            WHERE CAST(supervisor_id AS TEXT) IN ({placeholders})
            GROUP BY CAST(supervisor_id AS TEXT)
            """,
            tuple(member_ids),
        ).fetchall()
        for r in count_rows:
            store_counts_by_supervisor[str(r['supervisor_id_text'])] = r['c']

    # Attach store_count to each team member
    for m in team_members:
        m['store_count'] = int(store_counts_by_supervisor.get(str(m.get('honor_id')), 0))

    for member in team_members:
        role_name = (member.get('user_type_name') or '').upper()
        member['is_ambassador'] = ('AMBASSADOR' in role_name)

    promoters_count = sum(1 for m in team_members if m.get('is_ambassador'))

    # Convert pending stores to dict format
    pending_stores_data = []
    for store in pending_stores:
        store_dict = {
            'id': store.id,
            'store_name': store.store_name,
            'store_code': store.store_code,
            'company': store.company.name if store.company else 'N/A',
            'city_name': store.city.name if store.city else 'N/A',
            'province_name': store.province.name if store.province else 'N/A',
            'market_center': store.market_center.name if store.market_center else 'N/A',
            'level': store.level,
            'local': store.local,
            'street': store.street
        }
        pending_stores_data.append(store_dict)

    # Convert pending clients to dict format
    pending_clients_data = []
    for client in pending_clients:
        client_dict = {
            'id': client.id,
            'name': client.name,
            'client_id': client.client_id,
            'gender': client.gender,
            'contact_number': client.contact_number,
            'email': client.email,
            'city_name': client.city.name if client.city else 'N/A',
            'province_name': client.province.name if client.province else 'N/A'
        }
        pending_clients_data.append(client_dict)

    conn.close()

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
def dashboard_debug():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()

    # Samples and counts
    stores_count = conn.execute(
        'SELECT COUNT(1) as c FROM stores WHERE CAST(supervisor_id AS TEXT) = ? OR UPPER(CAST(supervisor_id AS TEXT)) = UPPER(?) OR LOWER(CAST(supervisor_id AS TEXT)) = LOWER(?)',
        (session['user_id'], session['user_id'], session['user_id'])
    ).fetchone()['c']

    team_members = conn.execute(
        '''
        SELECT u.id AS honor_id, u.name, u.user_type_id, u.supervisor_id, ut.name AS user_type_name
        FROM users u JOIN user_types ut ON u.user_type_id = ut.id
        WHERE CAST(u.supervisor_id AS TEXT) = ?
           OR UPPER(CAST(u.supervisor_id AS TEXT)) = UPPER(?)
           OR LOWER(CAST(u.supervisor_id AS TEXT)) = LOWER(?)
        LIMIT 50
        ''',
        (session['user_id'], session['user_id'], session['user_id'])
    ).fetchall()

    any_users = conn.execute(
        'SELECT id, name, user_type_id, supervisor_id FROM users LIMIT 50'
    ).fetchall()

    pending_stores_count = conn.execute(
        'SELECT COUNT(1) as c FROM pending_stores WHERE CAST(supervisor_id AS TEXT) = ? OR UPPER(CAST(supervisor_id AS TEXT)) = UPPER(?) OR LOWER(CAST(supervisor_id AS TEXT)) = LOWER(?) AND status = "PENDING"',
        (session['user_id'], session['user_id'], session['user_id'])
    ).fetchone()['c']

    pending_clients_count = conn.execute(
        'SELECT COUNT(1) as c FROM pending_clients WHERE CAST(supervisor_id AS TEXT) = ? OR UPPER(CAST(supervisor_id AS TEXT)) = UPPER(?) OR LOWER(CAST(supervisor_id AS TEXT)) = LOWER(?) AND status = "PENDING"',
        (session['user_id'], session['user_id'], session['user_id'])
    ).fetchone()['c']

    conn.close()

    team_members_list = [dict(r) for r in team_members]
    any_users_list = [dict(r) for r in any_users]

    promoters_count = sum(1 for m in team_members_list if 'AMBASSADOR' in (m.get('user_type_name') or '').upper())

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
def create_store_page():
    """Simple store creation form"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
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
def create_salesman_page():
    """Simple salesman creation form"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
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
def assignments_page():
    """Assignment manager with dual-list UI"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    from ..extensions import db
    from ..models import Stores, PendingStores
    from sqlalchemy.orm import joinedload
    
    # Get all stores (active and pending) for the supervisor
    active_stores = db.session.query(Stores).options(
        joinedload(Stores.company),
        joinedload(Stores.city),
        joinedload(Stores.province)
    ).filter(
        Stores.supervisor_id == session['user_id']
    ).all()
    
    pending_stores = db.session.query(PendingStores).options(
        joinedload(PendingStores.company),
        joinedload(PendingStores.city),
        joinedload(PendingStores.province)
    ).filter(
        PendingStores.supervisor_id == session['user_id'],
        PendingStores.status == 'PENDING'
    ).all()
    
    return render_template('assignments.html',
                         active_stores=active_stores,
                         pending_stores=pending_stores)


@dashboard_bp.route('/admin/approvals')
def admin_approvals_page():
    """Admin interface for approving pending assignments"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Check if user is admin (you may need to adjust this based on your user type logic)
    from ..extensions import db
    from ..models import User
    
    user = db.session.query(User).filter_by(id=session['user_id']).first()
    
    # Check if user is admin (adjust this condition based on your user_type logic)
    if not user or user.user_type_id != 1:  # Assuming 1 is admin
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('admin_approvals.html')


