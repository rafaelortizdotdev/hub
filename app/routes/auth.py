from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from ..database import get_db_connection

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return redirect(url_for('dashboard.dashboard'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        honor_id = (request.form.get('id') or '').strip()
        password = (request.form.get('password') or '').strip()

        if not honor_id or not password:
            flash('Por favor ingrese tanto el ID de Honor como la contraseña', 'error')
            return redirect(url_for('auth.login'))

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE UPPER(id) = UPPER(?) AND user_type_id = 1 AND status = "ACTIVE"',
            (honor_id,)
        ).fetchone()
        conn.close()

        if not user:
            flash('Credenciales incorrectas o usuario no encontrado', 'error')
            return redirect(url_for('auth.login'))

        stored_password = user['password_hash'] if 'password_hash' in user.keys() else 'honor1##'
        if password != stored_password:
            flash('Contraseña incorrecta', 'error')
            return redirect(url_for('auth.login'))

        session['user_id'] = user['id']
        session['honor_id'] = user['id']
        session['name'] = user['name']
        session['user_type'] = 'SUPERVISOR'
        flash('Inicio de sesión exitoso', 'success')
        return redirect(url_for('dashboard.dashboard'))

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Ha sido desconectado', 'info')
    return redirect(url_for('auth.login'))


