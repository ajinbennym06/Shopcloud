from flask import Blueprint, render_template, request
from app.models import Product, Category

products_bp = Blueprint('products', __name__)


@products_bp.route('/')
def index():
    category_id = request.args.get('category', type=int)
    search      = request.args.get('q', '').strip()
    page        = request.args.get('page', 1, type=int)

    query = Product.query.filter_by(is_active=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    products   = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=12)
    categories = Category.query.all()
    return render_template('products/index.html', products=products, categories=categories,
                           selected_category=category_id, search=search)


@products_bp.route('/products/<int:product_id>')
def detail(product_id):
    product = Product.query.filter_by(id=product_id, is_active=True).first_or_404()
    related = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True
    ).limit(4).all()
    return render_template('products/detail.html', product=product, related=related)
