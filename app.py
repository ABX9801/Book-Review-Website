import os
import requests, json
from flask import Flask, session, request, render_template
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not 'postgres://imowektmwpmarg:863ced98e8498885468ae8318f7765f4ba688fb808dc095be6d6487ba9744d5c@ec2-52-0-155-79.compute-1.amazonaws.com:5432/d9rhdrliov37cm':
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine('postgres://imowektmwpmarg:863ced98e8498885468ae8318f7765f4ba688fb808dc095be6d6487ba9744d5c@ec2-52-0-155-79.compute-1.amazonaws.com:5432/d9rhdrliov37cm')
db = scoped_session(sessionmaker(bind=engine))


@app.route("/",methods=["GET", "POST"])
def homepage():
    session.clear()
    return render_template('homepage.html',)

@app.route('/login',methods=["GET", "POST"])
def login():

    return render_template('login.html')

@app.route('/signup',methods=["GET", "POST"])
def signup():
    return render_template('signup.html')

@app.route('/success',methods=["POST"])
def success():
    session.clear()
    # register user
    username = request.form.get('uname')
    password = request.form.get('psw')
    user = db.execute('SELECT * FROM users WHERE username=:username',{'username':username}).fetchone()

    if user is not None:
        return render_template('error.html',message='user already exists')
    
    db.execute('INSERT INTO users (username , password) VALUES (:username, :password)',{'username':username,'password':password})
    db.commit()

    return render_template('success.html',username=username,password=password)


@app.route('/review', methods=['POST'])
def review():
    session.clear()
    #login
    username = request.form.get('username')
    password = request.form.get('password')

    user = db.execute('SELECT * FROM users WHERE username=:username',{'username':username}).fetchone()
    if user is None:
        return render_template('error.html',message='user not registered')
    key = user.password

    if password!=key:
        return render_template('error.html',message='wrong password')
    
    session['username'] = username

    return render_template('review.html',username=session['username'])

@app.route('/search',methods=['POST'])
def search():

    search = request.form.get('search')
    search = search.title()
    search = '%'+ search + '%'
    
    rows = db.execute(' SELECT * FROM books WHERE title LIKE :search OR isbn LIKE :search OR author LIKE :search',{'search':search})
    
    if rows.rowcount == 0:
        return render_template("error.html", message="we can't find books with that description.")
    
    books = rows.fetchall()

    return render_template("results.html", books=books,username=session['username'])

@app.route('/book/<isbn>', methods=['GET','POST'])
def book(isbn):

    book = db.execute('SELECT * FROM books WHERE isbn = :isbn ',{'isbn':isbn}).fetchone()

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "IuhREfkEOZCyEdd50WxDA", "isbns": book.isbn })
    res = res.json()

    res = res['books'][0]
    
    review = request.form.get('review')
    rating = request.form.get('rating')

    if review and rating is not None:
        username = session['username']
        user = db.execute('SELECT * FROM users WHERE username = :username',{'username':username}).fetchone()
        user_id = user.id
        book = db.execute('SELECT * FROM books WHERE isbn = :isbn ',{'isbn':isbn}).fetchone()
        book_id = book.id
        
        review_existing = db.execute('SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id',{'user_id':user_id,'book_id':book_id}).fetchone()
        if review_existing is not None:
            return render_template('error.html',message='You have already submitted the review')
        db.execute('INSERT INTO reviews (user_id,book_id,text,rating) VALUES (:user_id, :book_id, :text, :rating)',{'user_id':user_id,'book_id':book_id,'text':review,'rating':rating})
        db.commit()

        reviews = db.execute('SELECT * FROM users JOIN reviews ON users.id=reviews.user_id WHERE book_id = :book_id',{'book_id':book_id}).fetchall()
        
    else:
        book = db.execute('SELECT * FROM books WHERE isbn = :isbn ',{'isbn':isbn}).fetchone()
        book_id = book.id
        reviews=db.execute('SELECT * FROM users JOIN reviews ON users.id=reviews.user_id WHERE book_id = :book_id',{'book_id':book_id}).fetchall()
        
    
    return render_template('book.html',message=res,username=session['username'],title = book.title,author=book.author,reviews=reviews)
