from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, Product, Order, Category
from app.utils import upload_to_s3, delete_from_s3

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Admin access required.', 'danger')
            return redirect(url_for('products.index'))
        return f(*args, **kwargs)
    return login_required(decorated)


@admin_bp.route('/')
@admin_required
def dashboard():
    stats = {
        'users':    User.query.count(),
        'products': Product.query.count(),
        'orders':   Order.query.count(),
        'revenue':  db.session.query(db.func.sum(Order.total_amount)).scalar() or 0,
    }
    recent_orders = Order.query.order_by(Order.ordered_at.desc()).limit(10).all()
    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders)


# ── Products ─────────────────────────────────────────────────────────────────

@admin_bp.route('/products')
@admin_required
def products():
    all_products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin/products.html', products=all_products)


@admin_bp.route('/products/new', methods=['GET', 'POST'])
@admin_required
def product_new():
    categories = Category.query.all()
    if request.method == 'POST':
        image_url = None
        if 'image' in request.files and request.files['image'].filename:
            image_url = upload_to_s3(request.files['image'])

        product = Product(
            name=request.form['name'].strip(),
            description=request.form.get('description', '').strip(),
            price=float(request.form['price']),
            stock=int(request.form.get('stock', 0)),
            category_id=request.form.get('category_id') or None,
            image_url=image_url,
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added.', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', product=None, categories=categories)


@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def product_edit(product_id):
    product    = Product.query.get_or_404(product_id)
    categories = Category.query.all()
    if request.method == 'POST':
        product.name        = request.form['name'].strip()
        product.description = request.form.get('description', '').strip()
        product.price       = float(request.form['price'])
        product.stock       = int(request.form.get('stock', 0))
        product.category_id = request.form.get('category_id') or None
        product.is_active   = 'is_active' in request.form

        if 'image' in request.files and request.files['image'].filename:
            if product.image_url:
                delete_from_s3(product.image_url)
            product.image_url = upload_to_s3(request.files['image'])

        db.session.commit()
        flash('Product updated.', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', product=product, categories=categories)


@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@admin_required
def product_delete(product_id):
    product = Product.query.get_or_404(product_id)
    if product.image_url:
        delete_from_s3(product.image_url)
    product.is_active = False   # soft delete
    db.session.commit()
    flash('Product removed.', 'info')
    return redirect(url_for('admin.products'))


# ── Orders ────────────────────────────────────────────────────────────────────

@admin_bp.route('/orders')
@admin_required
def orders():
    all_orders = Order.query.order_by(Order.ordered_at.desc()).all()
    return render_template('admin/orders.html', orders=all_orders)


@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def order_status(order_id):
    order  = Order.query.get_or_404(order_id)
    status = request.form.get('status')
    if status in ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled'):
        order.status = status
        db.session.commit()
        flash(f'Order #{order_id} marked as {status}.', 'success')
    return redirect(url_for('admin.orders'))


# ── Users ─────────────────────────────────────────────────────────────────────

@admin_bp.route('/users')
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@admin_required
def user_toggle(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot deactivate your own account.', 'danger')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        flash(f'User {"activated" if user.is_active else "deactivated"}.', 'info')
    return redirect(url_for('admin.users'))


# ── Categories ────────────────────────────────────────────────────────────────

@admin_bp.route('/categories', methods=['GET', 'POST'])
@admin_required
def categories():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if name and not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name))
            db.session.commit()
            flash('Category added.', 'success')
        else:
            flash('Category name empty or already exists.', 'danger')
    all_cats = Category.query.all()
    return render_template('admin/categories.html', categories=all_cats)
