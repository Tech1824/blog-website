from app import app
from model import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    u = User.query.filter_by(Email='author@blognest.com').first()
    if u:
        u.role        = 'admin'
        u.is_verified = True
        u.Password    = generate_password_hash('Author@123')
        db.session.commit()
        print('✅ Admin fixed!')
        print('   Email:    author@blognest.com')
        print('   Password: Author@123')
        print('   Role:     admin')
        print('   Verified: True')
    else:
        print('❌ User not found')