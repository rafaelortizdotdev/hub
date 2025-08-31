#!/usr/bin/env python3
"""
Honor Supervisor Hub - Flask Application
Flask app for supervisors to manage their stores and teams
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///honor_hub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('honor_hub.db')
    conn.row_factory = sqlite3.Row
    return conn

# User model for SQLAlchemy
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
    status = db.Column(db.String)
    password_hash = db.Column(db.String, nullable=False, default='honor1##')  # Default password
    is_first_login = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        honor_id = request.form['honor_id'].strip()
        password = request.form['password'].strip()
        
        if honor_id and password:
            conn = get_db_connection()
            user = conn.execute(
                'SELECT * FROM users WHERE UPPER(honor_id) = UPPER(?) AND user_type_id = 1 AND status = "ACTIVE"',
                (honor_id,)
            ).fetchone()
            conn.close()
            
            if user:
                # Check if user has custom password or using default
                stored_password = user['password_hash'] if 'password_hash' in user.keys() else 'honor1##'
                
                if password == stored_password:
                    session['user_id'] = user['id']
                    session['honor_id'] = user['honor_id']
                    session['name'] = user['name']
                    session['user_type'] = 'SUPERVISOR'
                    
                    # Handle SQLite Row object - check if column exists and get value
                    is_first_login = True  # Default value
                    if 'is_first_login' in user.keys():
                        is_first_login = bool(user['is_first_login'])
                    
                    # Always redirect to dashboard (password change removed for now)
                    flash('Login successful!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid password', 'error')
            else:
                flash('Invalid credentials or user not found', 'error')
        else:
            flash('Please enter both honor ID and password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get supervisor's stores
    stores_rows = conn.execute('''
        SELECT s.*, c.name as city_name, p.name as province_name 
        FROM stores s 
        JOIN cities c ON s.city_id = c.id 
        JOIN provinces p ON s.province_id = p.id 
        WHERE s.supervisor_id = ?
    ''', (session['user_id'],)).fetchall()
    
    # Get supervisor's team members
    team_members_rows = conn.execute('''
        SELECT u.*, ut.name as user_type_name 
        FROM users u 
        JOIN user_types ut ON u.user_type_id = ut.id 
        WHERE u.supervisor_id = ?
    ''', (session['user_id'],)).fetchall()
    
    # Get pending stores
    pending_stores_rows = conn.execute('''
        SELECT * FROM pending_stores WHERE supervisor_id = ? AND status = 'PENDING'
    ''', (session['user_id'],)).fetchall()
    
    # Get pending clients
    pending_clients_rows = conn.execute('''
        SELECT * FROM pending_clients WHERE supervisor_id = ? AND status = 'PENDING'
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    # Convert SQLite Row objects to dictionaries for template rendering
    stores = []
    for row in stores_rows:
        stores.append(dict(row))
    
    team_members = []
    for row in team_members_rows:
        team_members.append(dict(row))
    
    pending_stores = []
    for row in pending_stores_rows:
        pending_stores.append(dict(row))
    
    pending_clients = []
    for row in pending_clients_rows:
        pending_clients.append(dict(row))
    
    return render_template('dashboard.html', 
                         stores=stores, 
                         team_members=team_members,
                         pending_stores=pending_stores,
                         pending_clients=pending_clients)

@app.route('/api/stores')
def api_stores():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    stores = conn.execute('''
        SELECT s.*, c.name as city_name, p.name as province_name 
        FROM stores s 
        JOIN cities c ON s.city_id = c.id 
        JOIN provinces p ON s.province_id = p.id 
        WHERE s.supervisor_id = ?
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    stores_list = []
    for store in stores:
        stores_list.append(dict(store))
    
    return jsonify(stores_list)

# Old create_pending_store route removed - functionality moved to unified form

# Old create_pending_client route removed - functionality moved to unified form

@app.route('/approve-store/<int:store_id>', methods=['POST'])
def approve_store(store_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get the pending store
        store = cursor.execute('SELECT * FROM pending_stores WHERE id = ? AND supervisor_id = ?', 
                             (store_id, session['user_id'])).fetchone()
        
        if not store:
            return jsonify({'error': 'Store not found'}), 404
        
        # Here you would typically move the data to your main stores table
        # For now, we'll just mark it as approved
        cursor.execute('UPDATE pending_stores SET status = "APPROVED" WHERE id = ?', (store_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Store approved successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Password change functionality removed - will be added in future update

@app.route('/store-assignment')
def store_assignment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
            # Get available cities and states from provinces and cities tables
        conn = get_db_connection()
        geography_rows = conn.execute('''
            SELECT DISTINCT p.name as state, c.name as city 
            FROM provinces p 
            JOIN cities c ON c.province_id = p.id 
            ORDER BY p.name, c.name
        ''').fetchall()
        
        # Extract market centers dynamically from existing store names
        market_centers_rows = conn.execute('''
            SELECT DISTINCT 
                CASE 
                    WHEN store_name LIKE '%CC %' THEN 'CC'
                    WHEN store_name LIKE '%MERCADO %' THEN 'MERCADO'
                    ELSE 'OTHER'
                END as type,
                CASE 
                    WHEN store_name LIKE '%CC %' THEN 
                        SUBSTR(store_name, INSTR(store_name, 'CC ') + 3, 
                               INSTR(SUBSTR(store_name, INSTR(store_name, 'CC ') + 3), ' NIVEL') - 1)
                    WHEN store_name LIKE '%MERCADO %' THEN 
                        SUBSTR(store_name, INSTR(store_name, 'MERCADO ') + 8, 
                               INSTR(store_name, INSTR(store_name, 'MERCADO ') + 8), ' NIVEL') - 1)
                    ELSE ''
                END as name
            FROM stores 
            WHERE store_name LIKE '%CC %' OR store_name LIKE '%MERCADO %'
            ORDER BY type, name
        ''').fetchall()
    conn.close()
    
    # Convert SQLite Row objects to dictionaries for JSON serialization
    geography = []
    for row in geography_rows:
        geography.append({
            'state': row['state'],
            'city': row['city']
        })
    
    market_centers = []
    for row in market_centers_rows:
        market_centers.append(row['name'])
    
    return render_template('unified_store_client_form.html', geography=geography, market_centers=market_centers)

@app.route('/api/unified-store-client', methods=['POST'])
def api_unified_store_client():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Handle store creation/search
        store_id = None
        if data['store_action'] == 'create':
            # Create new pending store
            cursor.execute('''
                INSERT INTO pending_stores 
                (store_name, client_name, city, street, market_center, level, local, 
                 urban_municipality, state, capacity, sales_last_month, facade, 
                 table_available, supervisor_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
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
                session['user_id']
            ))
            store_id = cursor.lastrowid
        else:
            # Use selected store
            if not data['selected_store_id']:
                return jsonify({'error': 'Por favor selecciona una tienda existente' }), 400
            store_id = data['selected_store_id']
        
        # Handle client creation/search
        client_id = None
        if data['client_action'] == 'create':
            # Create new pending client
            cursor.execute('''
                INSERT INTO pending_clients 
                (name, client_id, passport, gender, contact_number, email, province, city, supervisor_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['client_name'],
                data['dni'],  # Use DNI as primary ID
                data.get('passport', ''),  # Passport is optional
                data['gender'],
                data['contact_number'],
                data['email'],
                data['province'],
                data['client_city'],
                session['user_id']
            ))
            client_id = cursor.lastrowid
        else:
            # Use selected client
            if not data['selected_client_id']:
                return jsonify({'error': 'Por favor selecciona un cliente existente' }), 400
            client_id = data['selected_client_id']
        
        # Create client-store relationships
        if data['assign_to_new_store'] and store_id:
            cursor.execute('''
                INSERT OR IGNORE INTO client_store (client_id, store_id, store_type, supervisor_id)
                VALUES (?, ?, ?, ?)
            ''', (client_id, store_id, 'pending' if data['store_action'] == 'create' else 'existing', session['user_id']))
        
        # Assign to existing stores
        if data['assign_to_existing_stores']:
            for existing_store_id in data['assign_to_existing_stores']:
                cursor.execute('''
                    INSERT OR IGNORE INTO client_store (client_id, store_id, store_type, supervisor_id)
                    VALUES (?, ?, ?, ?)
                ''', (client_id, existing_store_id, 'existing', session['user_id']))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Operación completada exitosamente'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/market-centers', methods=['POST'])
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
        
        # Check if market center already exists
        existing = cursor.execute('SELECT id FROM market_centers WHERE name = ?', (name,)).fetchone()
        if existing:
            return jsonify({'error': 'Mercado/CC ya existe'}), 409
        
        # Insert new market center
        cursor.execute('INSERT INTO market_centers (name) VALUES (?)', (name,))
        conn.commit()
        
        new_center = cursor.execute('SELECT * FROM market_centers WHERE id = ?', (cursor.lastrowid,)).fetchone()
        conn.close()
        
        return jsonify({'id': new_center['id'], 'name': new_center['name']})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-stores')
def api_search_stores():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    try:
        conn = get_db_connection()
        # Search in both stores and pending_stores tables
        stores = conn.execute('''
            SELECT id, store_name, store_code, city_id, 'existing' as type
            FROM stores 
            WHERE (store_code LIKE ? OR store_name LIKE ? OR company LIKE ?) 
            AND supervisor_id = ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%', session['user_id'])).fetchall()
        
        pending_stores = conn.execute('''
            SELECT id, store_name, 'PENDING' as store_code, city, 'pending' as type
            FROM pending_stores 
            WHERE (store_name LIKE ? OR client_name LIKE ?) 
            AND supervisor_id = ?
        ''', (f'%{query}%', f'%{query}%', session['user_id'])).fetchall()
        
        conn.close()
        
        # Convert to dictionaries
        results = []
        for store in stores:
            results.append(dict(store))
        for store in pending_stores:
            results.append(dict(store))
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-clients')
def api_search_clients():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    try:
        conn = get_db_connection()
        # Search in pending_clients table
        clients = conn.execute('''
            SELECT id, name, contact_number, city, province
            FROM pending_clients 
            WHERE (name LIKE ? OR contact_number LIKE ?) 
            AND supervisor_id = ?
        ''', (f'%{query}%', f'%{query}%', session['user_id'])).fetchall()
        
        conn.close()
        
        # Convert to dictionaries
        results = []
        for client in clients:
            results.append(dict(client))
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/approve-client/<int:client_id>', methods=['POST'])
def approve_client(client_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get the pending client
        client = cursor.execute('SELECT * FROM pending_clients WHERE id = ? AND supervisor_id = ?', 
                              (client_id, session['user_id'])).fetchone()
        
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        # Here you would typically move the data to your main users table
        # For now, we'll just mark it as approved
        cursor.execute('UPDATE pending_clients SET status = "APPROVED" WHERE id = ?', (client_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Client approved successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)

