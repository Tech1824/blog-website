from flask import Flask, redirect, render_template, request, url_for, flash, session,jsonify
from flask_sqlalchemy import SQLAlchemy
from config import config
from model import db, User, Post, Like, Comment, Category, PostTag, Bookmark
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from flask_login import login_user, LoginManager, login_required
import random
from datetime import date, datetime, timedelta
from functools import wraps

app = Flask(__name__, static_folder='static')
app.config.from_object(config)

# ---------- Mail config must come BEFORE Mail(app) 
app.config['MAIL_SERVER']   = 'smtp.gmail.com'
app.config['MAIL_PORT']     = 587
app.config['MAIL_USE_TLS']  = True
app.config['MAIL_USERNAME'] = 'admin227q@gmail.com'
app.config['MAIL_PASSWORD'] = 'hbeq vwao ycoh jdjk'
app.config['MAIL_DEBUG']    = True

mail = Mail(app)
db.init_app(app)

def time_ago(dt):
    if dt is None:
        return '—'
    now = datetime.utcnow()
    diff = now - dt
    if diff.days >= 1:
        return f"{diff.days}d ago"
    hours = diff.seconds // 3600
    if hours >= 1:
        return f"{hours}h ago"
    minutes = diff.seconds // 60
    if minutes >= 1:
        return f"{minutes}m ago"
    return "Just now"

app.jinja_env.filters['time_ago'] = time_ago

with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_Id):
    return User.query.get(int(user_Id))


# ------------------------------------ Admin decorator 

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            flash("Admin access required!", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# --------------------------------------Home 
@app.route('/')
def home():
    featured_posts = Post.query.filter_by(status='published')\
                               .order_by(Post.created_at.desc())\
                               .limit(3).all()
    return render_template('home.html', featured_posts=featured_posts)

#---------------------------about route
@app.route('/about')
def about():
    total_posts      = Post.query.filter_by(status='published').count()
    total_users      = User.query.count()
    total_categories = Category.query.count()
    total_comments   = Comment.query.count()
    return render_template('about.html',
        total_posts      = total_posts,
        total_users      = total_users,
        total_categories = total_categories,
        total_comments   = total_comments,
    )

#--------------------------------contacts route
@app.route('/contact', methods= ['POST'])
def contact():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name  = request.form.get('last_name', '').strip()
        email      = request.form.get('email', '').strip()
        subject    = request.form.get('subject', '').strip()
        message    = request.form.get('message', '').strip()

        try:
            msg = Message(
                subject    = f'[BlogNest Contact] {subject} from {first_name}',
                sender     = 'admin227q@gmail.com',
                recipients = ['admin227q@gmail.com'],
                body       = f'From: {first_name} {last_name}\nEmail: {email}\n\n{message}'
            )
            mail.send(msg)
            flash('Your message was sent! We will get back to you soon.', 'success')
        except Exception as e:
            print('Mail error:', e)
            flash('Something went wrong. Please try again later.', 'danger')

        return redirect(url_for('contact'))

    return render_template('contact.html')
#-------------------------------------- Register 
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        Username = request.form.get("Username")
        Email    = request.form.get("Email")
        Password = request.form.get("Password")
        Confirm  = request.form.get('confirm_password')

        if Password != Confirm:
            return render_template('register.html', error='Passwords not matched!')

        if User.query.filter_by(Email=Email).first():
            flash("Email Already exists!", "danger")
            return render_template("register.html", error="Email already registered!")

        new_user = User(
            Username   = Username,
            Email      = Email,
            Password   = generate_password_hash(Password),
            is_verified = False,
            role       = 'user',
            created_at = datetime.utcnow()
        )
        db.session.add(new_user)
        db.session.commit()

        otp = str(random.randint(100000, 999999))
        session['otp']     = otp
        session['user_Id'] = new_user.Id

        msg = Message(
            'Verify your Email',
            sender     = 'admin227q@gmail.com',
            recipients = [Email]
        )
        msg.body = f'Your OTP is {otp}\n\nIt expires in 5 minutes.'
        try:
            mail.send(msg)
        except Exception as e:
            print('Mail error:', e)

        return redirect(url_for('verify_otp'))
    return render_template('register.html')


# ---------------------------------------Verify OTP 
@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        if entered_otp == session.get('otp'):
            user = User.query.get(session['user_Id'])
            user.is_verified = True
            db.session.commit()
            session.pop('otp', None)
            session.pop('user_Id', None)
            return redirect(url_for('login'))
        else:
            return render_template('verify_otp.html', error='Invalid OTP! Try again.')
    return render_template('verify_otp.html')


#  --------------------------------------------Login 
@app.route('/login', methods=['GET', 'POST'])
def login():
    next_page = request.args.get('next') 
    if request.method == 'POST':
        Email    = request.form.get('Email')
        Password = request.form.get('Password')
        user     = User.query.filter_by(Email=Email).first()

        if user and check_password_hash(user.Password, Password):
            if not user.is_verified:
                flash('Please verify your email first.', 'warning')
                

                login_user(user)
                session['User_Id']  = user.Id
                session['username'] = user.Username 
                session['role']     = user.role
                if next_page:                              # ← redirect to category
                   return redirect(next_page)
                if user.role == 'admin':
                   return redirect(url_for('admin_dashboard'))
                else:
                   return redirect(url_for('user_dashboard'))
            return redirect(url_for('user_dashboard'))
    
    flash('Invalid credentials.', 'danger')
    return render_template('login.html')

#----------------------categories route
@app.route('/categories')
def categories():
    categories = Category.query.order_by(Category.Id).all()
    return render_template('categories.html', categories=categories)

#-----------------category posts

@app.route('/category/<int:cat_id>')
@login_required
def category_posts(cat_id):
    category = Category.query.get_or_404(cat_id)
    posts = Post.query.filter_by(
        category_Id=cat_id, status='published'
    ).order_by(Post.created_at.desc()).all()
    return render_template('category_post.html', category=category, posts=posts)
# -------------------------------Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
#------------------------------notification
@app.context_processor
def inject_notifications():
    count = 0
    if session.get('role') == 'admin':
        count = User.query.filter_by(is_verified=False).count()
    return dict(notification_count=count)


# -------------------------------- User Dashboard 
@app.route('/user_dashboard', methods=['GET', 'POST'])
def user_dashboard():
    user_Id = session.get('User_Id')
    if not user_Id:
        return redirect(url_for('login'))

    posts_read_count = Bookmark.query.filter_by(User_Id=user_Id).count()
    comments_count   = Comment.query.filter_by(User_Id=user_Id).count()
    liked_count      = Like.query.filter_by(User_Id=user_Id).count()
    bookmarks_count  = Bookmark.query.filter_by(User_Id=user_Id).count()

    last_read = (
        Post.query
        .join(Bookmark, Bookmark.post_Id == Post.Id)
        .filter(Bookmark.User_Id == user_Id)
        .order_by(Bookmark.Id.desc())
        .limit(4).all()
    )
    recent_comments = (
        Comment.query
        .filter_by(User_Id=user_Id)
        .order_by(Comment.created_at.desc())
        .limit(3).all()
    )
    liked_posts = (
        Like.query
        .filter_by(User_Id=user_Id)
        .order_by(Like.Id.desc())
        .limit(4).all()
    )

    return render_template("user_dashboard.html",
        posts_read_count = posts_read_count,
        comments_count   = comments_count,
        liked_count      = liked_count,
        bookmarks_count  = bookmarks_count,
        last_read        = last_read,
        recent_comments  = recent_comments,
        liked_posts      = liked_posts,
    )


#-----------------------------------Search 
@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    results = []
    if query:
        results = Post.query.filter(
            (Post.title.ilike(f'%{query}%')) |
            (Post.content.ilike(f'%{query}%'))
        ).all()
        # .filter_by(status='published').all()
    return render_template('search.html', results=results, query=query)

# ─--------------------------------Feed 
@app.route('/feed')
@login_required
def feed():
    posts = Post.query.filter_by(status='published')\
                      .order_by(Post.created_at.desc()).all()
    return render_template('feed.html', posts=posts)


# --------------------------- Saved / Bookmarks 
@app.route('/saved')
def saved():
    user_Id = session.get('User_Id')
    if not user_Id:
        return redirect(url_for('login'))
    
    role = session.get('role')  # 'admin' or 'user'
    
    bookmarks = Bookmark.query.filter_by(User_Id=user_Id)\
                              .order_by(Bookmark.Id.desc()).all()
    
    # Pass extra admin data if needed
    posts = Post.query.order_by(Post.created_at.desc()).all() if role == 'admin' else []
    categories = Category.query.order_by(Category.Id).all() if role == 'admin' else []

    return render_template('saved.html',
        bookmarks=bookmarks,
        last_read_posts=[],
        role=role,
        posts=posts,
        categories=categories,
    )
    


@app.route('/remove_bookmark/<int:bookmark_Id>', methods=['POST'])
def remove_bookmark(bookmark_Id):
    bookmark = Bookmark.query.get_or_404(bookmark_Id)
    db.session.delete(bookmark)
    db.session.commit()
    flash("Bookmark removed!", "success")
    return redirect(url_for('saved'))


# --------------------------------------- Profile 

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user_Id = session.get('User_Id')
    if not user_Id:
        return redirect(url_for('login'))

    user = User.query.get(user_Id)  # ← store object in 'user', keep 'user_Id' as int

    if request.method == 'POST':
        user.Username = request.form.get('Username', user.Username)
        user.Email    = request.form.get('Email', user.Email)
        new_password  = request.form.get('Password')
        if new_password:
            user.Password = generate_password_hash(new_password)
        db.session.commit()
        flash("Profile updated", "success")
        return redirect(url_for('profile'))

    comments_count  = Comment.query.filter_by(User_Id=user_Id).count() 
    liked_count     = Like.query.filter_by(User_Id=user_Id).count()      # int 
    bookmarks_count = Bookmark.query.filter_by(User_Id=user_Id).count()  # int 

    return render_template('profile.html',
        user            = user,
        comments_count  = comments_count,
        liked_count     = liked_count,
        bookmarks_count = bookmarks_count,
    )


# ----------------------------------- Settings 
@app.route('/settings', methods=['GET'])
def settings():
    user_Id = session.get('User_Id')
    if not user_Id:
        return redirect(url_for('login'))
    user = User.query.get(user_Id)  
    return render_template('settings.html', user=user)


@app.route('/settings/account', methods=['POST'])
def settings_account():
    user_Id = session.get('User_Id')
    if not user_Id:
        return redirect(url_for('login'))
    user = User.query.get(user_Id)  
    user.Username = request.form.get('Username', user.Username)
    user.Email    = request.form.get('Email', user.Email)
    db.session.commit()
    flash("Profile updated!", "success")
    return redirect(url_for('settings'))  


@app.route('/settings/password', methods=['POST'])
def settings_password():
    user_Id = session.get('User_Id')
    if not user_Id:
        return redirect(url_for('login'))
    user = User.query.get(user_Id)  
    current      = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm      = request.form.get('confirm_password')  
    if not check_password_hash(user.Password, current):  
        flash("Incorrect current password!", "danger")
        return redirect(url_for('settings'))

    if new_password != confirm:
        flash("Passwords do not match!", "danger")
        return redirect(url_for('settings'))

    user.Password = generate_password_hash(new_password)
    db.session.commit()  
    flash("Password updated!", "success")
    return redirect(url_for('settings'))


@app.route('/settings/delete_account', methods=['POST'])
def settings_delete_account():
    user_Id = session.get('User_Id')
    if not user_Id:
        return redirect(url_for('login'))
    user = User.query.get(user_Id)
    db.session.delete(user)
    db.session.commit()
    session.clear()
    return redirect(url_for('user'))


# --------------------------------------------Post Detail 
@app.route('/post/<int:post_Id>', methods=['GET'])
def post_detail(post_Id):
    post = Post.query.get_or_404(post_Id)

   
    comments = Comment.query.filter_by(post_Id=post_Id)\
                            .order_by(Comment.created_at.asc()).all()

    related_posts = Post.query.filter(
        Post.Id != post_Id,
        Post.status == 'published'
    ).limit(5).all()

    user_Id = session.get('User_Id')

    is_liked = Like.query.filter_by(
        post_Id=post_Id,
        User_Id=user_Id
        ).first() is not None if user_Id else False
    is_bookmarked = Bookmark.query.filter_by(
        post_Id=post_Id,
        User_Id=user_Id
        ).first() is not None if user_Id else False

    word_count = len(post.content.split())
    read_time  = max(1, round(word_count / 200))

    return render_template('post_detail.html',
        post          = post,
        comments      = comments,
        related_posts = related_posts,
        is_liked      = is_liked,
        is_bookmarked = is_bookmarked,
        read_time     = read_time,
    )
#---------------------------publish post
@app.route('/admin/post/publish/<int:post_Id>')
@login_required
def admin_publish_post(post_Id):
    post = Post.query.get_or_404(post_Id)
    post.status = 'published'
    db.session.commit()
    return redirect(url_for('admin_posts'))


#---------------------------------------- Like 

@app.route('/like/<int:post_Id>', methods=['POST'])
def add_like(post_Id):
    user_Id = session.get('User_Id')
    if not user_Id:
        return jsonify({'error': 'login_required'}), 401  # ← NOT redirect

    existing = Like.query.filter_by(post_Id=post_Id, User_Id=user_Id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        liked = False
    else:
        db.session.add(Like(post_Id=post_Id, User_Id=user_Id))
        db.session.commit()
        liked = True

    count = Like.query.filter_by(post_Id=post_Id).count()
    return jsonify({'liked': liked, 'count': count})  


@app.route('/bookmark/<int:post_Id>', methods=['POST'])
def add_bookmark(post_Id):
    user_Id = session.get('User_Id')
    if not user_Id:
        return jsonify({'error': 'login_required'}), 401

    existing = Bookmark.query.filter_by(post_Id=post_Id, User_Id=user_Id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        saved = False
    else:
        db.session.add(Bookmark(post_Id=post_Id, User_Id=user_Id))
        db.session.commit()
        saved = True

    return jsonify({'saved': saved})  


@app.route('/comment/<int:post_Id>', methods=['POST'])
def add_comment(post_Id):
    user_Id = session.get('User_Id')
    if not user_Id:
        return jsonify({'error': 'login_required'}), 401

    data = request.get_json()
    content = (data or {}).get('content', '').strip()
    if not content:
        return jsonify({'error': 'empty'}), 400

    comment = Comment(
        post_Id=post_Id,
        User_Id=user_Id,
        content=content,
        created_at=datetime.utcnow()
    )
    db.session.add(comment)
    db.session.commit()

    count = Comment.query.filter_by(post_Id=post_Id).count()
    return jsonify({
        'success': True,
        'count': count,
        'comment': {
            'username': comment.user.Username,
            'content': comment.content,
        }
    })

# --------------------------------- ADMIN ROUTES

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    total_users     = User.query.count()
    new_users_today = User.query.filter(
        User.created_at >= datetime.utcnow().date()  
    ).count()
    total_posts     = Post.query.count()
    published_posts = Post.query.filter_by(status='published').count()
    total_likes     = Like.query.count()
    total_comments  = Comment.query.count()

    recent_users    = User.query.order_by(User.Id.desc()).limit(6).all()
    recent_posts    = Post.query.order_by(Post.created_at.desc()).limit(6).all()
    recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(6).all()

    top_posts = sorted(
        Post.query.filter_by(status='published').all(),
        key=lambda p: len(p.likes),
        reverse=True
    )[:5]

    return render_template(
            'admin_dashboard.html',
            total_users     = total_users,
            new_users_today = new_users_today,
            total_posts     = total_posts,
            published_posts = published_posts,
            total_likes     = total_likes,
            total_comments  = total_comments,
            recent_users    = recent_users,
            recent_posts    = recent_posts,
            recent_comments = recent_comments,
            top_posts       = top_posts,
    )
    
@app.route('/admin/users')  
@admin_required
def admin_users():
    users = User.query.order_by(User.Id.desc()).all()
    return render_template('admin_users.html', users=users)  


@app.route('/admin/users/<int:user_Id>/role', methods=['POST'])
@admin_required
def admin_change_role(user_Id):
    user     = User.query.get_or_404(user_Id)
    new_role = request.form.get('role')
    if new_role in ['user', 'author', 'admin']:
        user.role = new_role
        db.session.commit()
        flash(f'{user.Username} is now {new_role}.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/users/<int:user_Id>/delete', methods=['POST'])
@admin_required
def admin_delete_user(user_Id):
    user = User.query.get_or_404(user_Id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted", "success")
    return redirect(url_for('admin_users'))

@app.route('/admin/posts/<int:post_Id>/toggle', methods=['POST'])
@admin_required
def admin_toggle_post(post_Id):
    post = Post.query.get_or_404(post_Id)
    post.status = 'draft' if post.status == 'published' else 'published'  
    db.session.commit()
    flash(f'Post {"published" if post.status == "published" else "unpublished"}.', 'success')
    return redirect(url_for('admin_posts'))


@app.route('/admin/comments')
@admin_required
def admin_comments():
    
    comments = Comment.query.order_by(Comment.created_at.desc()).all()
    return render_template('admin_comments.html', comments=comments)


@app.route('/admin/comments/<int:comment_Id>/delete', methods=['POST'])
@admin_required
def admin_delete_comment(comment_Id):
    comment = Comment.query.get_or_404(comment_Id)
    db.session.delete(comment)
    db.session.commit()
    flash("Comment deleted!", "success")
    return redirect(url_for('admin_comments'))


@app.route('/admin/categories')
@login_required
def admin_categories():
    categories = Category.query.all()
    cat_counts = [len(cat.posts) for cat in categories]
    return render_template('admin_categories.html', 
                           categories=categories,
                           cat_counts=cat_counts)


@app.route('/admin/categories/create', methods=['POST'])
@admin_required
def admin_create_category(): 
    name        = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash("Name field required!", "danger")
        return redirect(url_for('admin_categories'))

    if Category.query.filter_by(name=name).first():
        flash("Category already exists!", "warning")
        return redirect(url_for('admin_categories'))

    category = Category(name=name, description=description)
    db.session.add(category)
    db.session.commit()
    flash(f'Category "{name}" created!', 'success')
    return redirect(url_for('admin_categories'))  


@app.route('/admin/categories/<int:category_Id>/edit', methods=['POST'])
@admin_required
def admin_edit_category(category_Id):
    category             = Category.query.get_or_404(category_Id)
    category.name        = request.form.get('name', category.name).strip()
    category.description = request.form.get('description', '').strip()
    db.session.commit()
    flash("Category updated!", "success")
    return redirect(url_for('admin_categories'))


@app.route('/admin/categories/<int:category_Id>/delete', methods=['POST'])
@admin_required
def admin_delete_category(category_Id):
    category = Category.query.get_or_404(category_Id)
    db.session.delete(category)
    db.session.commit()
    flash("Category deleted!", "success")
    return redirect(url_for('admin_categories'))

@app.route('/admin/posts')
@admin_required
def admin_posts():
    posts      = Post.query.order_by(Post.created_at.desc()).all()
    categories = Category.query.order_by(Category.Id).all()  
    return render_template('admin_posts.html', posts=posts, categories=categories)

#-------------------------create post

import re

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text.strip())
    return text


@app.route('/admin/posts/create', methods=['GET', 'POST'])
@admin_required
def admin_create_post():
    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        slug  = slugify(title)
        content     = request.form.get('content', '').strip()
        status      = request.form.get('status', 'draft')
        category_Id = request.form.get('category_Id') or None   # ← capital Id
        thumbnail   = request.form.get('thumbnail', '').strip() or None
        excerpt     = request.form.get('excerpt', '').strip() or None

        if not title or not content:
            flash("Title and content are required!", "danger")
            categories = Category.query.order_by(Category.Id).all()
            users = User.query.order_by(User.Id).all()
            return render_template('admin_create_post.html', categories=categories, users=users, post=None)

        post = Post(
            title       = title,
            slug        = slug,
            content     = content,
            status      = status,
            category_Id = int(category_Id) if category_Id else None,  # ← capital Id
            author_id   = session.get('User_Id'),
            thumbnail   = thumbnail,   # ← was cover_image, now thumbnail
            excerpt     = excerpt,
            created_at  = datetime.utcnow()
        )
        db.session.add(post)
        db.session.commit()
        flash(f'Post "{title}" created!', 'success')
        return redirect(url_for('admin_posts'))

    categories = Category.query.order_by(Category.Id).all()
    users      = User.query.order_by(User.Id).all()
    return render_template('admin_create_post.html', categories=categories, users=users, post=None)


@app.route('/admin/posts/<int:post_Id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_post(post_Id):
    post = Post.query.get_or_404(post_Id)

    if request.method == 'POST':
        post.title       = request.form.get('title', post.title).strip()
        post.content     = request.form.get('content', post.content).strip()
        post.status      = request.form.get('status', post.status)
        category_Id      = request.form.get('category_Id') or None
        post.category_Id = int(category_Id) if category_Id else None
        thumbnail        = request.form.get('thumbnail', '').strip()
        excerpt          = request.form.get('excerpt', '').strip()
        if thumbnail:
            post.thumbnail = thumbnail
        if excerpt:
            post.excerpt = excerpt
        db.session.commit()
        flash(f'Post "{post.title}" updated!', 'success')
        return redirect(url_for('admin_posts'))

    # GET — open the rich editor pre-filled with this post's data
    categories = Category.query.order_by(Category.Id).all()
    users      = User.query.order_by(User.Id).all()
    return render_template('admin_create_post.html', post=post, categories=categories, users=users)
#--------------------------setting notication
@app.route('/settings/notifications', methods=['POST'])
def settings_notifications():
    user_Id = session.get('User_Id')
    if not user_Id:
        return redirect(url_for('login'))
   
    flash("Notification preferences saved!", "success")
    return redirect(url_for('settings'))

if __name__ == "__main__":
    app.run(debug=True, threaded=False, use_reloader=False)