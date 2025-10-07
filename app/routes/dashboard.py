from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify

from ..database import get_db_connection

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
        JOIN regions p ON s.province_id = p.id 
        WHERE (
            CAST(s.supervisor_id AS TEXT) = ?
            OR UPPER(CAST(s.supervisor_id AS TEXT)) = UPPER(?)
            OR LOWER(CAST(s.supervisor_id AS TEXT)) = LOWER(?)
        )
        ''',
        (session['user_id'], session['user_id'], session['user_id']),
    ).fetchall()

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

    pending_stores_rows = conn.execute(
        '''
        SELECT * FROM pending_stores WHERE (
            CAST(supervisor_id AS TEXT) = ?
            OR UPPER(CAST(supervisor_id AS TEXT)) = UPPER(?)
            OR LOWER(CAST(supervisor_id AS TEXT)) = LOWER(?)
        ) AND status = 'PENDING'
        ''',
        (session['user_id'], session['user_id'], session['user_id']),
    ).fetchall()

    pending_clients_rows = conn.execute(
        '''
        SELECT * FROM pending_clients WHERE (
            CAST(supervisor_id AS TEXT) = ?
            OR UPPER(CAST(supervisor_id AS TEXT)) = UPPER(?)
            OR LOWER(CAST(supervisor_id AS TEXT)) = LOWER(?)
        ) AND status = 'PENDING'
        ''',
        (session['user_id'], session['user_id'], session['user_id']),
    ).fetchall()

    # Compute store counts per team member (by supervisor_id matching member.honor_id)
    stores = [dict(r) for r in stores_rows]
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

    pending_stores = [dict(r) for r in pending_stores_rows]
    pending_clients = [dict(r) for r in pending_clients_rows]

    conn.close()

    return render_template(
        'dashboard.html',
        stores=stores,
        team_members=team_members,
        promoters_count=promoters_count,
        pending_stores=pending_stores,
        pending_clients=pending_clients,
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

@dashboard_bp.route('/store-assignment')
def store_assignment():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()

    geography_rows = conn.execute(
        '''
        SELECT DISTINCT p.name as state, c.name as city 
        FROM regions p, cities c
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


