from app import app
from model import db, User
from werkzeug.security import generate_password_hash
from datetime import datetime

with app.app_context():
    # Show which DB we're using
    print("Using DB:", app.config['SQLALCHEMY_DATABASE_URI'])
    
    existing = User.query.filter_by(Email='author@blognest.com').first()
    if existing:
        print("Found existing user, updating to admin...")
        existing.role        = 'admin'
        existing.is_verified = True
        existing.Password    = generate_password_hash('Author@123')
        db.session.commit()
        print('✅ Updated to admin!')
    else:
        admin = User(
            Username    = 'Admin',
            Email       = 'author@blognest.com',
            Password    = generate_password_hash('Author@123'),
            is_verified = True,
            role        = 'admin',
            created_at  = datetime.utcnow()
        )
        db.session.add(admin)
        db.session.commit()
        print('✅ Admin created!')

    u = User.query.filter_by(Email='author@blognest.com').first()
    print('Username:', u.Username)
    print('Role    :', u.role)
    print('Verified:', u.is_verified)