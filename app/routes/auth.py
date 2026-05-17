from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
import jwt
import datetime
import re

auth_bp = Blueprint('auth', __name__)

# Simple in-memory rate limiter for login attempts
_login_attempts = {}

def _check_rate_limit(ip):
    now = datetime.datetime.utcnow()
    attempts = _login_attempts.get(ip, [])
    attempts = [t for t in attempts if (now - t).seconds < 300]  # 5-min window
    _login_attempts[ip] = attempts
    return len(attempts) >= 5   # block after 5 attempts

def _record_attempt(ip):
    _login_attempts.setdefault(ip, []).append(datetime.datetime.utcnow())


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('products.index'))
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        # Basic validation
        if not all([name, email, password]):
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html')
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            flash('Invalid email address.', 'danger')
            return render_template('auth/register.html')
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('auth/register.html')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('products.index'))
    if request.method == 'POST':
        ip = request.remote_addr
        if _check_rate_limit(ip):
            flash('Too many login attempts. Please wait 5 minutes.', 'danger')
            return render_template('auth/login.html')

        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()

        if user and user.is_active and user.check_password(password):
            login_user(user, remember=True)
            # Issue JWT stored in HttpOnly cookie
            token = jwt.encode({
                'user_id': user.id,
                'role': user.role,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')
            resp = make_response(redirect(request.args.get('next') or url_for('products.index')))
            resp.set_cookie('auth_token', token, httponly=True, secure=True, samesite='Lax', max_age=86400)
            return resp
        else:
            _record_attempt(ip)
            flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    resp = make_response(redirect(url_for('auth.login')))
    resp.delete_cookie('auth_token')
    flash('You have been logged out.', 'info')
    return resp
