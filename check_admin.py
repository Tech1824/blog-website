from app import app
from model import User

with app.app_context():
    print("Using DB:", app.config['SQLALCHEMY_DATABASE_URI'])
    
    all_users = User.query.all()
    print(f"Total users in DB: {len(all_users)}")
    for u in all_users:
        print(f"  - {u.Username} | {u.Email} | role={u.role} | verified={u.is_verified}")