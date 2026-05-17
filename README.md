# ShopCloud — E-Commerce Capstone (DevSecOps)

A secure, cloud-native E-Commerce web application built with Flask + MySQL, deployed on AWS using DevSecOps best practices.

## Tech stack
- **Backend:** Python Flask 3, SQLAlchemy ORM
- **Database:** MySQL (AWS RDS)
- **Auth:** Flask-Login, bcrypt password hashing, JWT in HttpOnly cookies
- **Storage:** AWS S3 (product images) + CloudFront CDN
- **Security:** CSRF protection, XSS headers, rate limiting, RBAC
- **Server:** Ubuntu EC2 + Nginx reverse proxy
- **CI/CD:** GitHub Actions → EC2

## Local setup

```bash
git clone https://github.com/yourusername/shopcloud.git
cd shopcloud

# Create virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DB and AWS credentials

# Run database migrations
flask db init
flask db migrate -m "initial"
flask db upgrade

# Seed admin user + categories
flask seed

# Start the app
python run.py
```

Visit http://localhost:5000

Admin panel: http://localhost:5000/admin  
Default admin: `admin@shopcloud.com` / `Admin@1234`

## EC2 Deployment

1. SSH into your EC2 instance
2. Clone this repo to `/app`
3. Copy `.env` with production values (RDS endpoint, S3 bucket, etc.)
4. Copy `nginx.conf` to `/etc/nginx/sites-available/shopcloud` and enable it
5. Create a systemd service for the app
6. Run `flask db upgrade && flask seed`
7. Add `scripts/backup.sh` to cron for nightly DB backups

## Security features implemented
- bcrypt password hashing (cost factor 12)
- JWT authentication in HttpOnly + Secure cookies
- CSRF protection on all forms (Flask-WTF)
- SQL injection prevention via SQLAlchemy ORM
- XSS protection via Content-Security-Policy headers
- Rate limiting on login (5 attempts / 5 minutes)
- Role-Based Access Control (customer / admin)
- HTTPS enforced via Nginx + Let's Encrypt / AWS ACM
- Security headers: HSTS, X-Frame-Options, X-Content-Type-Options
# Shopcloud
