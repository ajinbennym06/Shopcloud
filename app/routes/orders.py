from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Cart, Order, OrderItem, Product

orders_bp = Blueprint('orders', __name__)


@orders_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    items = Cart.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart.view'))

    total = sum(item.product.price * item.quantity for item in items)

    if request.method == 'POST':
        address = request.form.get('address', '').strip()
        if not address:
            flash('Delivery address is required.', 'danger')
            return render_template('orders/checkout.html', items=items, total=total)

        # Check stock and create order
        for item in items:
            if item.quantity > item.product.stock:
                flash(f'Not enough stock for "{item.product.name}".', 'danger')
                return render_template('orders/checkout.html', items=items, total=total)

        order = Order(user_id=current_user.id, total_amount=total, address=address)
        db.session.add(order)
        db.session.flush()   # get order.id before commit

        for item in items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.product.price,
            )
            item.product.stock -= item.quantity
            db.session.add(order_item)
            db.session.delete(item)

        db.session.commit()
        flash(f'Order #{order.id} placed successfully!', 'success')
        return redirect(url_for('orders.history'))

    return render_template('orders/checkout.html', items=items, total=total)


@orders_bp.route('/orders')
@login_required
def history():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.ordered_at.desc()).all()
    return render_template('orders/history.html', orders=user_orders)


@orders_bp.route('/orders/<int:order_id>')
@login_required
def detail(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return render_template('orders/detail.html', order=order)
