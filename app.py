from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_socketio import SocketIO, join_room, emit
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
from contextlib import closing

app = Flask(__name__)
app.secret_key = "super_secret_key"
socketio = SocketIO(app, async_mode="threading")

DATABASE = "database.db"


# ================= DATABASE =================
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(get_db()) as conn:
        cur = conn.cursor()

        # USERS
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
        """)

        # GROUPS
        cur.execute("""
        CREATE TABLE IF NOT EXISTS groups(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            created_by TEXT
        )
        """)

        # GROUP MEMBERS
        cur.execute("""
        CREATE TABLE IF NOT EXISTS group_members(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT,
            username TEXT
        )
        """)

        # GROUP MESSAGES
        cur.execute("""
        CREATE TABLE IF NOT EXISTS group_messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT,
            sender TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ✅ PRIVATE MESSAGES (FIX)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS private_messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()


init_db()


# ================= LOGIN REQUIRED =================
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "username" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return wrap


# ================= AUTH =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].lower()
        email = request.form["email"].lower()
        password = generate_password_hash(request.form["password"])

        with closing(get_db()) as conn:
            cur = conn.cursor()

            if cur.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone():
                return "User exists"

            role = "admin" if cur.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0 else "employee"

            cur.execute("INSERT INTO users(username,email,password,role) VALUES(?,?,?,?)",
                        (username, email, password, role))
            conn.commit()

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].lower()
        password = request.form["password"]

        with closing(get_db()) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username=?", (username,))
            user = cur.fetchone()

        if user and check_password_hash(user["password"], password):
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect("/")

        return "Invalid login"

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/login")


# ================= HOME =================
@app.route("/")
@login_required
def home():
    username = session["username"]

    with closing(get_db()) as conn:
        cur = conn.cursor()

        cur.execute("SELECT username FROM users WHERE username!=?", (username,))
        users = [u["username"] for u in cur.fetchall()]

        cur.execute("SELECT group_name FROM group_members WHERE username=?", (username,))
        groups = [g["group_name"] for g in cur.fetchall()]

    return render_template("chat.html",
                           username=username,
                           users=users,
                           groups=groups,
                           role=session["role"])


# ================= ADMIN =================
@app.route("/admin")
@login_required
def admin():
    if session["role"] != "admin":
        return "Unauthorized", 403

    with closing(get_db()) as conn:
        cur = conn.cursor()

        cur.execute("SELECT username, role FROM users")
        users = cur.fetchall()

        cur.execute("SELECT name FROM groups")
        groups = [g["name"] for g in cur.fetchall()]

    return render_template("admin.html", users=users, groups=groups)


@app.route("/admin/create_group", methods=["POST"])
@login_required
def create_group():
    if session["role"] != "admin":
        return "Unauthorized", 403

    name = request.form["group_name"]

    with closing(get_db()) as conn:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO groups(name,created_by) VALUES(?,?)",
                        (name, session["username"]))
            conn.commit()
        except:
            pass

    return redirect("/admin")


# ================= GROUP CHAT =================
@app.route("/group/<group_name>")
@login_required
def group_chat(group_name):
    username = session["username"]

    with closing(get_db()) as conn:
        cur = conn.cursor()

        cur.execute("""
        SELECT 1 FROM group_members
        WHERE group_name=? AND username=?
        """, (group_name, username))

        if not cur.fetchone():
            return "Access Denied"

        cur.execute("SELECT sender,message FROM group_messages WHERE group_name=?",
                    (group_name,))
        messages = cur.fetchall()

    return render_template("group.html",
                           group=group_name,
                           username=username,
                           messages=messages,
                           room=f"group_{group_name}")


# ================= ✅ PRIVATE CHAT (FIXED) =================
@app.route("/dm/<username>")
@login_required
def dm(username):
    current_user = session["username"]

    with closing(get_db()) as conn:
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM users WHERE username=?", (username,))
        if not cur.fetchone():
            return "User not found"

        cur.execute("""
        SELECT sender,message FROM private_messages
        WHERE (sender=? AND receiver=?)
        OR (sender=? AND receiver=?)
        ORDER BY timestamp
        """, (current_user, username, username, current_user))

        messages = cur.fetchall()

    room = f"dm_{current_user}_{username}"

    return render_template("private_chat.html",
                           username=current_user,
                           receiver=username,
                           messages=messages,
                           room=room)


# ================= SOCKET =================
@socketio.on("join")
def join(data):
    join_room(data["room"])


# GROUP MESSAGE
@socketio.on("send_message")
def send_group(data):
    room = data["room"]
    sender = data["sender"]
    message = data["message"]

    group = room.replace("group_", "")

    with closing(get_db()) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO group_messages(group_name,sender,message) VALUES(?,?,?)",
                    (group, sender, message))
        conn.commit()

    emit("receive_message", data, to=room)


# ✅ PRIVATE MESSAGE SOCKET
@socketio.on("private_message")
def private_message(data):
    sender = data["sender"]
    receiver = data["receiver"]
    message = data["message"]

    room1 = f"dm_{sender}_{receiver}"
    room2 = f"dm_{receiver}_{sender}"

    with closing(get_db()) as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO private_messages(sender,receiver,message)
        VALUES(?,?,?)
        """, (sender, receiver, message))
        conn.commit()

    emit("receive_private_message", data, to=room1)
    emit("receive_private_message", data, to=room2)


# ================= RUN =================
if __name__ == "__main__":
    socketio.run(app, debug=True, port=5050)