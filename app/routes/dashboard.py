from flask import Blueprint, render_template, redirect, url_for, session

from ..db import get_db_connection

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()

    stores_rows = conn.execute(
        '''
        SELECT s.*, c.name as city_name, p.name as province_name 
        FROM stores s 
        JOIN cities c ON s.city_id = c.id 
        JOIN provinces p ON s.province_id = p.id 
        WHERE s.supervisor_id = ?
        ''',
        (session['user_id'],),
    ).fetchall()

    team_members_rows = conn.execute(
        '''
        SELECT u.*, ut.name as user_type_name 
        FROM users u 
        JOIN user_types ut ON u.user_type_id = ut.id 
        WHERE u.supervisor_id = ?
        ''',
        (session['user_id'],),
    ).fetchall()

    pending_stores_rows = conn.execute(
        '''
        SELECT * FROM pending_stores WHERE supervisor_id = ? AND status = 'PENDING'
        ''',
        (session['user_id'],),
    ).fetchall()

    pending_clients_rows = conn.execute(
        '''
        SELECT * FROM pending_clients WHERE supervisor_id = ? AND status = 'PENDING'
        ''',
        (session['user_id'],),
    ).fetchall()

    conn.close()

    stores = [dict(r) for r in stores_rows]
    team_members = [dict(r) for r in team_members_rows]
    pending_stores = [dict(r) for r in pending_stores_rows]
    pending_clients = [dict(r) for r in pending_clients_rows]

    return render_template(
        'dashboard.html',
        stores=stores,
        team_members=team_members,
        pending_stores=pending_stores,
        pending_clients=pending_clients,
    )


@dashboard_bp.route('/store-assignment')
def store_assignment():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()

    geography_rows = conn.execute(
        '''
        SELECT DISTINCT p.name as state, c.name as city 
        FROM provinces p 
        JOIN cities c ON c.province_id = p.id 
        ORDER BY p.name, c.name
        '''
    ).fetchall()

    try:
        market_centers_rows = conn.execute(
            'SELECT DISTINCT name FROM market_centers ORDER BY name'
        ).fetchall()
    except Exception:
        market_centers_rows = []

    conn.close()

    geography = [{'state': r['state'], 'city': r['city']} for r in geography_rows]
    market_centers = [r['name'] for r in market_centers_rows]

    return render_template(
        'unified_store_client_form.html',
        geography=geography,
        market_centers=market_centers,
    )


