import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required, logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY environment variable is not set!")

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
if not app.config['SQLALCHEMY_DATABASE_URI']:
    raise RuntimeError("DATABASE_URL environment variable is not set!")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

from flask_migrate import Migrate
migrate = Migrate(app, db)


# the google books API Key (it uses environment variables for security)
API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")
if not API_KEY:
    raise ValueError("Please set the GOOGLE_BOOKS_API_KEY environment variable.")

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    cover_image = db.Column(db.String(300), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# User Loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('signup'))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('intro'))

@app.route('/')
def intro():
    
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template('intro.html')  

@app.route('/home')

@login_required
def home():
    books = Book.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', books=books)


@app.route('/add', methods=['POST'])
@login_required
def add_book():
    book_name = request.form['book_name']
    metadata = get_book_metadata(book_name)
    if metadata:
        new_book = Book(title=metadata["title"], cover_image=metadata["cover_image"], user_id=current_user.id)
        db.session.add(new_book)
        db.session.commit()
        flash('Book added successfully!', 'success')
    else:
        flash('Book not found.', 'danger')
    return redirect(url_for('home') + "?scroll=true")  # Add scroll query parameter

@app.route('/delete/<int:book_id>', methods=['POST'])
@login_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    if book.user_id != current_user.id:
        flash("You don't have permission to delete this book.", 'danger')
        return redirect(url_for('home'))
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted successfully!', 'success')
    return redirect(url_for('home') + "?scroll=true")  # Add scroll query parameter



@app.route('/suggest', methods=['GET'])
def suggest():
    query = request.args.get('q')
    if query:
        url = f"https://www.googleapis.com/books/v1/volumes?q={query}&key={API_KEY}&maxResults=5"
        response = requests.get(url)
        suggestions = []
        if response.status_code == 200:
            data = response.json()
            if 'items' in data:
                for item in data['items']:
                    title = item['volumeInfo'].get('title', 'No Title')
                    cover_image = item['volumeInfo'].get('imageLinks', {}).get('thumbnail', '')
                    suggestions.append({"title": title, "cover_image": cover_image})
        return {"suggestions": suggestions}
    return {"suggestions": []}


# Google Books API Integration
def get_book_metadata(book_name):
    url = f"https://www.googleapis.com/books/v1/volumes?q={book_name}&key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "items" in data:
            book = data["items"][0]
            title = book["volumeInfo"]["title"]
            cover_image = book["volumeInfo"].get("imageLinks", {}).get("thumbnail", "No Image Available")
            return {"title": title, "cover_image": cover_image}
    return None

if __name__ == "__main__":
    # it creates the database tables if they don't exist
    with app.app_context():
        db.create_all()
    app.run(debug=True)
