from app import create_app, db
from app.models import User, Product, Category, Order, OrderItem, Cart

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Product=Product, Category=Category,
                Order=Order, OrderItem=OrderItem, Cart=Cart)

@app.cli.command('seed')
def seed_db():
    """Seed the database with an admin user and sample categories."""
    # Admin user
    if not User.query.filter_by(email='admin@shopcloud.com').first():
        admin = User(name='Admin', email='admin@shopcloud.com', role='admin')
        admin.set_password('Admin@1234')
        db.session.add(admin)

    # Sample categories
    for cat_name in ['Electronics', 'Clothing', 'Books', 'Home & Kitchen', 'Sports']:
        if not Category.query.filter_by(name=cat_name).first():
            db.session.add(Category(name=cat_name))

    db.session.commit()
    print('Database seeded.')
    print('Admin login: admin@shopcloud.com / Admin@1234')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
