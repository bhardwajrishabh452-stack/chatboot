from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "super_secret_key"


# ================= DATABASE =================
def get_db():
    conn = sqlite3.connect("chat.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # USERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user',
        status TEXT DEFAULT 'active'
    )
    """)

    # MESSAGES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        message TEXT
    )
    """)

    # TEAMS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    )
    """)

    # TEAM MEMBERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS team_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_id INTEGER,
        user_id INTEGER
    )
    """)

    # DEFAULT ADMIN
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
            ("admin", "admin@gmail.com", generate_password_hash("admin123"), "admin")
        )

    conn.commit()
    conn.close()


# ================= AUTH =================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") not in ["admin", "superadmin"]:
            return redirect(url_for("chat_section", section="chat"))
        return f(*args, **kwargs)
    return wrapper


# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = generate_password_hash(request.form["password"])

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, password)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username or Email already exists!"

        return redirect(url_for("login"))

    return render_template("register.html")


# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user["password"], password):
            if user["status"] != "active":
                return "Account is disabled!"

            session["username"] = user["username"]
            session["role"] = user["role"]

            return redirect(url_for("chat_section", section="chat"))

        return "Invalid username or password!"

    return render_template("login.html")


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ================= MAIN =================
@app.route("/chat/<section>", methods=["GET", "POST"])
@login_required
def chat_section(section):
    conn = get_db()
    cursor = conn.cursor()

    # USERS
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    # CHAT
    messages = []
    if section == "chat":
        if request.method == "POST":
            receiver = request.form["receiver"]
            message = request.form["message"]

            if receiver and message:
                cursor.execute(
                    "INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)",
                    (session["username"], receiver, message)
                )
                conn.commit()

        cursor.execute("""
            SELECT * FROM messages
            WHERE sender=? OR receiver=?
            ORDER BY id ASC
        """, (session["username"], session["username"]))
        messages = cursor.fetchall()

    # ================= ADMIN =================
    all_users = []
    total_users = 0
    active_users = 0

    if section == "admin":
        if session.get("role") not in ["admin", "superadmin"]:
            return redirect(url_for("chat_section", section="chat"))

        cursor.execute("SELECT * FROM users")
        all_users = cursor.fetchall()

        # STATS
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE status='active'")
        active_users = cursor.fetchone()[0]

    # ================= TEAM =================
    teams = []
    team_members_map = {}

    if section == "team":
        cursor.execute("SELECT * FROM teams")
        teams = cursor.fetchall()

        for team in teams:
            cursor.execute("""
                SELECT users.username FROM team_members
                JOIN users ON users.id = team_members.user_id
                WHERE team_members.team_id=?
            """, (team["id"],))
            team_members_map[team["id"]] = cursor.fetchall()

    conn.close()

    return render_template(
        "chat.html",
        section=str(section),
        users=users,
        messages=messages,
        all_users=all_users,
        teams=teams,
        team_members_map=team_members_map,
        total_users=total_users,
        active_users=active_users
    )


# ================= TEAM =================
@app.route("/create_team", methods=["POST"])
@login_required
@admin_required
def create_team():
    name = request.form["team_name"]
    members = request.form.getlist("members")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO teams (name) VALUES (?)", (name,))
    team_id = cursor.lastrowid

    for user_id in members:
        cursor.execute(
            "INSERT INTO team_members (team_id, user_id) VALUES (?, ?)",
            (team_id, user_id)
        )

    conn.commit()
    conn.close()

    return redirect(url_for("chat_section", section="team"))


@app.route("/edit_team", methods=["POST"])
@login_required
@admin_required
def edit_team():
    team_id = request.form["team_id"]
    name = request.form["team_name"]
    members = request.form.getlist("members")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("UPDATE teams SET name=? WHERE id=?", (name, team_id))
    cursor.execute("DELETE FROM team_members WHERE team_id=?", (team_id,))

    for user_id in members:
        cursor.execute(
            "INSERT INTO team_members (team_id, user_id) VALUES (?, ?)",
            (team_id, user_id)
        )

    conn.commit()
    conn.close()

    return redirect(url_for("chat_section", section="team"))


@app.route("/delete_team/<int:team_id>")
@login_required
@admin_required
def delete_team(team_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM teams WHERE id=?", (team_id,))
    cursor.execute("DELETE FROM team_members WHERE team_id=?", (team_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("chat_section", section="team"))


# ================= ADMIN =================
@app.route("/delete_user/<int:user_id>")
@login_required
@admin_required
def delete_user(user_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT username FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()

    if user["username"] == session.get("username"):
        return "You cannot delete yourself!"

    if user["username"] == "admin":
        return "Main admin cannot be deleted!"

    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("chat_section", section="admin"))


@app.route("/toggle_user/<int:user_id>")
@login_required
@admin_required
def toggle_user(user_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT status FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()

    new_status = "inactive" if user["status"] == "active" else "active"

    cursor.execute("UPDATE users SET status=? WHERE id=?", (new_status, user_id))

    conn.commit()
    conn.close()

    return redirect(url_for("chat_section", section="admin"))


# CHANGE ROLE 🔥
@app.route("/change_role/<int:user_id>")
@login_required
@admin_required
def change_role(user_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT role, username FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()

    if user["username"] == session.get("username"):
        return "You cannot change your own role!"

    new_role = "admin" if user["role"] == "user" else "user"

    cursor.execute("UPDATE users SET role=? WHERE id=?", (new_role, user_id))

    conn.commit()
    conn.close()

    return redirect(url_for("chat_section", section="admin"))


# ================= RUN =================
if __name__ == "__main__":
    init_db()
    app.run(debug=True)