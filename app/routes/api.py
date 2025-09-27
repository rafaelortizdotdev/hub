from flask import Blueprint, jsonify, request, session

from ..database import get_db_connection

api_bp = Blueprint('api', __name__)


@api_bp.route('/stores')
def api_stores():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    stores = conn.execute(
        '''
        SELECT s.*, c.name as city_name, p.name as province_name 
        FROM stores s 
        JOIN cities c ON s.city_id = c.id 
        JOIN provinces p ON s.province_id = p.id 
        WHERE s.supervisor_id = ?
        ''',
        (session['user_id'],),
    ).fetchall()
    conn.close()

    stores_list = [dict(row) for row in stores]
    return jsonify(stores_list)


@api_bp.route('/market-centers', methods=['POST'])
def api_market_centers():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        if not name:
            return jsonify({'error': 'Nombre requerido'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        existing = cursor.execute(
            'SELECT id FROM market_centers WHERE name = ?', (name,)
        ).fetchone()
        if existing:
            return jsonify({'error': 'Mercado/CC ya existe'}), 409

        cursor.execute('INSERT INTO market_centers (name) VALUES (?)', (name,))
        conn.commit()
        new_center = cursor.execute(
            'SELECT * FROM market_centers WHERE id = ?', (cursor.lastrowid,)
        ).fetchone()
        conn.close()

        return jsonify({'id': new_center['id'], 'name': new_center['name']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/search-stores')
def api_search_stores():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    try:
        conn = get_db_connection()
        stores = conn.execute(
            '''
            SELECT id, store_name, store_code, city_id, 'existing' as type
            FROM stores 
            WHERE (store_code LIKE ? OR store_name LIKE ? OR company LIKE ?) 
            AND supervisor_id = ?
            ''',
            (f'%{query}%', f'%{query}%', f'%{query}%', session['user_id']),
        ).fetchall()

        pending_stores = conn.execute(
            '''
            SELECT id, store_name, 'PENDING' as store_code, city, 'pending' as type
            FROM pending_stores 
            WHERE (store_name LIKE ? OR client_name LIKE ?) 
            AND supervisor_id = ?
            ''',
            (f'%{query}%', f'%{query}%', session['user_id']),
        ).fetchall()

        conn.close()

        results = [dict(s) for s in stores] + [dict(s) for s in pending_stores]
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/search-clients')
def api_search_clients():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    try:
        conn = get_db_connection()
        clients = conn.execute(
            '''
            SELECT id, name, contact_number, city, province
            FROM pending_clients 
            WHERE (name LIKE ? OR contact_number LIKE ?) 
            AND supervisor_id = ?
            ''',
            (f'%{query}%', f'%{query}%', session['user_id']),
        ).fetchall()
        conn.close()

        results = [dict(c) for c in clients]
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/approve-store/<int:store_id>', methods=['POST'])
def approve_store(store_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        store = cursor.execute(
            'SELECT * FROM pending_stores WHERE id = ? AND supervisor_id = ?',
            (store_id, session['user_id']),
        ).fetchone()
        if not store:
            return jsonify({'error': 'Store not found'}), 404

        cursor.execute(
            'UPDATE pending_stores SET status = "APPROVED" WHERE id = ?', (store_id,)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Store approved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/approve-client/<int:client_id>', methods=['POST'])
def approve_client(client_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        client = cursor.execute(
            'SELECT * FROM pending_clients WHERE id = ? AND supervisor_id = ?',
            (client_id, session['user_id']),
        ).fetchone()
        if not client:
            return jsonify({'error': 'Client not found'}), 404

        cursor.execute(
            'UPDATE pending_clients SET status = "APPROVED" WHERE id = ?', (client_id,)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Client approved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/unified-store-client', methods=['POST'])
def api_unified_store_client():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()

        conn = get_db_connection()
        cursor = conn.cursor()

        store_id = None
        if data['store_action'] == 'create':
            cursor.execute(
                '''
                INSERT INTO pending_stores 
                (store_name, client_name, city, street, market_center, level, local, 
                 urban_municipality, state, capacity, sales_last_month, facade, 
                 table_available, supervisor_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    data['store_name'],
                    data['company'],
                    data['city'],
                    data['street'],
                    data['market_center'],
                    data['level'],
                    data['local'],
                    data['urban_municipality'],
                    data['state'],
                    int(data['capacity']) if data['capacity'] else None,
                    int(data['sales_last_month']) if data['sales_last_month'] else None,
                    data['facade'],
                    data['table'],
                    session['user_id'],
                ),
            )
            store_id = cursor.lastrowid
        else:
            if not data['selected_store_id']:
                return jsonify({'error': 'Por favor selecciona una tienda existente'}), 400
            store_id = data['selected_store_id']

        client_id = None
        if data['client_action'] == 'create':
            cursor.execute(
                '''
                INSERT INTO pending_clients 
                (name, client_id, passport, gender, contact_number, email, province, city, supervisor_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    data['client_name'],
                    data['dni'],
                    data.get('passport', ''),
                    data['gender'],
                    data['contact_number'],
                    data['email'],
                    data['province'],
                    data['client_city'],
                    session['user_id'],
                ),
            )
            client_id = cursor.lastrowid
        else:
            if not data['selected_client_id']:
                return jsonify({'error': 'Por favor selecciona un cliente existente'}), 400
            client_id = data['selected_client_id']

        if data['assign_to_new_store'] and store_id:
            cursor.execute(
                '''
                INSERT OR IGNORE INTO client_store (client_id, store_id, store_type, supervisor_id)
                VALUES (?, ?, ?, ?)
                ''',
                (
                    client_id,
                    store_id,
                    'pending' if data['store_action'] == 'create' else 'existing',
                    session['user_id'],
                ),
            )

        if data['assign_to_existing_stores']:
            for existing_store_id in data['assign_to_existing_stores']:
                cursor.execute(
                    '''
                    INSERT OR IGNORE INTO client_store (client_id, store_id, store_type, supervisor_id)
                    VALUES (?, ?, ?, ?)
                    ''',
                    (client_id, existing_store_id, 'existing', session['user_id']),
                )

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Operación completada exitosamente'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


