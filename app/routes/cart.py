from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Cart, Product

cart_bp = Blueprint('cart', __name__)


@cart_bp.route('/cart')
@login_required
def view():
    items = Cart.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in items)
    return render_template('cart/view.html', items=items, total=total)


@cart_bp.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add(product_id):
    product = Product.query.filter_by(id=product_id, is_active=True).first_or_404()
    qty = int(request.form.get('quantity', 1))
    if qty < 1 or qty > product.stock:
        flash('Invalid quantity.', 'danger')
        return redirect(url_for('products.detail', product_id=product_id))

    item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if item:
        item.quantity = min(item.quantity + qty, product.stock)
    else:
        item = Cart(user_id=current_user.id, product_id=product_id, quantity=qty)
        db.session.add(item)
    db.session.commit()
    flash(f'"{product.name}" added to cart.', 'success')
    return redirect(url_for('products.detail', product_id=product_id))


@cart_bp.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update(item_id):
    item = Cart.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    qty = int(request.form.get('quantity', 1))
    if qty < 1:
        db.session.delete(item)
    else:
        item.quantity = min(qty, item.product.stock)
    db.session.commit()
    return redirect(url_for('cart.view'))


@cart_bp.route('/cart/remove/<int:item_id>', methods=['POST'])
@login_required
def remove(item_id):
    item = Cart.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart.view'))
