from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# the database model
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    cover_image = db.Column(db.String(300), nullable=True)

# this is the google books API integration
def get_book_metadata(book_name):
    api_key = "AIzaSyB8tzLoWAxjhY5XSAFctuVHB_RG4kBV4Ww" 
    url = f"https://www.googleapis.com/books/v1/volumes?q={book_name}&key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "items" in data:
            book = data["items"][0]
            title = book["volumeInfo"]["title"]
            cover_image = book["volumeInfo"].get("imageLinks", {}).get("thumbnail", "No Image Available")
            return {"title": title, "cover_image": cover_image}
    return None


@app.route('/')
def home():
    books = Book.query.all()  
    return render_template('index.html', books=books)

@app.route('/suggest', methods=['GET'])
def suggest():
    query = request.args.get('q')  
    if query:
        api_key = "AIzaSyB8tzLoWAxjhY5XSAFctuVHB_RG4kBV4Ww"  
        url = f"https://www.googleapis.com/books/v1/volumes?q={query}&key={api_key}&maxResults=5"
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



@app.route('/add', methods=['POST'])
def add_book():
    book_name = request.form['book_name']
    metadata = get_book_metadata(book_name)
    if metadata:
        # it saves book data to the database
        new_book = Book(title=metadata["title"], cover_image=metadata["cover_image"])
        db.session.add(new_book)
        db.session.commit()
    return redirect(url_for('home'))

@app.route('/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    # it finds the book by ID and delete it
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for('home'))

if __name__ == "__main__":
    # it creates the database tables if they don't exist
    with app.app_context():
        db.create_all()
    app.run(debug=True)
