from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
import random

def genarate_employee_Id():
    return "EMP" + str(random.randint(10000, 999999))

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "user"
    Id          = db.Column(db.Integer, primary_key=True)
    Username    = db.Column(db.String(100), unique=True)
    Email       = db.Column(db.String(150), unique=True)
    Password    = db.Column(db.String(255))
    role        = db.Column(db.String(20), default='user')
    avatar      = db.Column(db.String(255), nullable=True)
    bio         = db.Column(db.String(300), nullable=True)
    is_active   = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    comments  = db.relationship('Comment',  backref='author',   lazy=True)
    likes     = db.relationship('Like',     backref='user',     lazy=True)
    bookmarks = db.relationship('Bookmark', backref='user',     lazy=True)

    def get_id(self):
        return str(self.Id)


class Post(db.Model):
    __tablename__ = "post"
    Id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200))
    slug        = db.Column(db.String(200), unique=True)
    content     = db.Column(db.Text)
    excerpt     = db.Column(db.String(300))
    thumbnail   = db.Column(db.String(255), nullable=True)   # ← renamed from cover_image
    status      = db.Column(db.String(20), default='draft')
    views       = db.Column(db.Integer, default=0)
    author_id   = db.Column(db.Integer, db.ForeignKey('user.Id'))
    category_Id = db.Column(db.Integer, db.ForeignKey('category.Id'))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationships
    author   = db.relationship('User',    backref='posts',    foreign_keys=[author_id])
    comments = db.relationship('Comment', backref='post',     lazy=True, cascade='all, delete-orphan')
    likes    = db.relationship('Like',    backref='post',     lazy=True, cascade='all, delete-orphan')
    bookmarks= db.relationship('Bookmark',backref='post',     lazy=True, cascade='all, delete-orphan')
    tags     = db.relationship('Tag',     secondary='posttag',backref='posts', lazy=True)


class Category(db.Model):
    __tablename__ = "category"
    Id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), unique=True)
    slug        = db.Column(db.String(100), unique=True, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    icon        = db.Column(db.String(50),  nullable=True)
    posts       = db.relationship('Post', backref='category', lazy=True,
                                  foreign_keys='Post.category_Id')


class Comment(db.Model):
    __tablename__ = "comment"
    Id         = db.Column(db.Integer, primary_key=True)
    content    = db.Column(db.Text)
    User_Id    = db.Column(db.Integer, db.ForeignKey('user.Id'))
    post_Id    = db.Column(db.Integer, db.ForeignKey('post.Id'))
    parent_id  = db.Column(db.Integer, db.ForeignKey('comment.Id'), nullable=True)
    is_flagged = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    

class Tag(db.Model):
    __tablename__ = "tag"
    Id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    slug = db.Column(db.String(50), unique=True, nullable=True)


class PostTag(db.Model):
    __tablename__ = "posttag"
    Id      = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.Id'))
    tag_id  = db.Column(db.Integer, db.ForeignKey('tag.Id'))


class Like(db.Model):
    __tablename__ = "like"
    Id         = db.Column(db.Integer, primary_key=True)
    User_Id    = db.Column(db.Integer, db.ForeignKey('user.Id'))
    post_Id    = db.Column(db.Integer, db.ForeignKey('post.Id'))  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Bookmark(db.Model):
    __tablename__ = "bookmark"
    Id         = db.Column(db.Integer, primary_key=True)
    User_Id    = db.Column(db.Integer, db.ForeignKey('user.Id'))
    post_Id    = db.Column(db.Integer, db.ForeignKey('post.Id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)