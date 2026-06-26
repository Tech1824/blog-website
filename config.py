from urllib.parse import quote_plus

password = quote_plus("Sharma@@1")  # actual password

class config:
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:{password}@127.0.0.1:3306/blog_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "secret123"