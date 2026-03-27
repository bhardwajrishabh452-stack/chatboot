import os
from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, join_room, emit
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "secretkey123"

# Create a folder for the database if it doesn't exist
db_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "database")
os.makedirs(db_folder, exist_ok=True)

# Absolute path to SQLite DB
db_path = os.path.join(db_folder, "chat.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app)

# User and Message models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50), nullable=False)
    receiver = db.Column(db.String(50), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Create tables safely inside app context
with app.app_context():
    db.create_all()

# Login Route
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            session['user'] = user.username
            return redirect(url_for('chat'))
        else:
            return render_template("login.html", error="Incorrect username or password")
    return render_template("login.html")

# Register Route
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if User.query.filter_by(username=request.form['username']).first():
            return render_template("register.html", error="Username already exists")
        new_user = User(
            username=request.form['username'],
            email=request.form['email'],
            password=request.form['password']
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template("register.html")

# Chat Route
@app.route("/chat")
def chat():
    if 'user' not in session:
        return redirect(url_for('login'))
    # Delete messages older than 72 hours
    expiry = datetime.utcnow() - timedelta(hours=72)
    Message.query.filter(Message.timestamp < expiry).delete()
    db.session.commit()
    messages = Message.query.order_by(Message.timestamp).all()
    return render_template("chat.html", messages=messages)

# Logout
@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# SocketIO
@socketio.on("join_room")
def join(data):
    join_room(data['room'])

@socketio.on("send_message")
def handle_message(data):
    msg = Message(sender=data['user'], receiver=data['room'], text=data['text'])
    db.session.add(msg)
    db.session.commit()
    # Emit message to sender and receiver
    emit("receive_message", data, room=data['room'])
    emit("receive_message", data, room=data['user'])

if __name__ == "__main__":
    socketio.run(app, debug=True)