from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from ..models import User, UserType

auth_bp = Blueprint('auth', __name__)


@auth_bp.before_app_request
def enforce_first_login():
    if session.get('is_first_login') and request.endpoint and not request.endpoint.startswith('auth.'):
        return redirect(url_for('auth.change_password'))


@auth_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return redirect(url_for('dashboard.dashboard'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = (request.form.get('id') or '').strip()
        password = (request.form.get('password') or '').strip()

        if not user_id or not password:
            flash('Por favor ingrese su ID y contraseña', 'error')
            return redirect(url_for('auth.login'))

        user = db.session.query(User).filter(
            db.func.upper(User.id) == user_id.upper(),
            User.status == 'ACTIVE'
        ).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash('Credenciales incorrectas', 'error')
            return redirect(url_for('auth.login'))

        user_type = db.session.query(UserType).filter_by(id=user.user_type_id).first()
        user_type_name = user_type.name if user_type else 'UNKNOWN'

        session.clear()
        session['user_id'] = user.id
        session['name'] = user.name
        session['user_type'] = user_type_name
        session['is_first_login'] = user.is_first_login

        if user.is_first_login:
            return redirect(url_for('auth.change_password'))

        flash('Inicio de sesión exitoso', 'success')
        return redirect(url_for('dashboard.dashboard'))

    return render_template('login.html')


@auth_bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        new_password = (request.form.get('new_password') or '').strip()
        confirm_password = (request.form.get('confirm_password') or '').strip()

        if not new_password or len(new_password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres', 'error')
            return redirect(url_for('auth.change_password'))

        if new_password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return redirect(url_for('auth.change_password'))

        user = db.session.query(User).filter_by(id=session['user_id']).first()
        user.password_hash = generate_password_hash(new_password)
        user.is_first_login = False
        db.session.commit()

        session['is_first_login'] = False
        flash('Contraseña actualizada exitosamente', 'success')
        return redirect(url_for('dashboard.dashboard'))

    return render_template('change_password.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Ha sido desconectado', 'info')
    return redirect(url_for('auth.login'))


