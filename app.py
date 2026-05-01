from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "super_secret_key"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# ================= DATABASE =================
def get_db():
    conn = sqlite3.connect("chat.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # USERS TABLE (with team_id)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user',
        status TEXT DEFAULT 'active',
        team_id INTEGER
    )
    """)

    # 🔥 FIX for old DB (adds column if missing)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN team_id INTEGER")
    except:
        pass



    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       sender TEXT,
       receiver TEXT,
       message TEXT,
       file TEXT,
      image TEXT,
      voice TEXT,
      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
     is_read INTEGER DEFAULT 0
    )
    """)
    
    try:
       cursor.execute("ALTER TABLE messages ADD COLUMN file TEXT")
    except:
      pass

    try:
      cursor.execute("ALTER TABLE messages ADD COLUMN image TEXT")
    except:
     pass

    try:
     cursor.execute("ALTER TABLE messages ADD COLUMN voice TEXT")
    except:
     pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS team_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_id INTEGER,
        user_id INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user',
        status TEXT DEFAULT 'active',
        team_id INTEGER,
        last_seen DATETIME
    )
    """) 
    try:
     cursor.execute("ALTER TABLE users ADD COLUMN last_seen DATETIME")
    except:
     pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS group_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER,
        user_id INTEGER
    )
    """)

    # CREATE DEFAULT ADMIN
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, email, password, role, status) VALUES (?, ?, ?, ?, ?)",
            ("admin", "admin@gmail.com", generate_password_hash("admin123"), "admin", "active")
        )

    conn.commit()
    conn.close()


# ================= AUTH =================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") not in ["admin", "superadmin"]:
            flash("Admin access required!", "danger")
            return redirect(url_for("chat_section", section="chat"))
        return f(*args, **kwargs)
    return wrapper


# ================= REGISTER =================
@app.route('/register', methods=['GET', 'POST'])
def register():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM teams")
    teams = cursor.fetchall()

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        team_id = request.form.get('team_id')

        try:
            # ✅ Insert into users table
            cursor.execute("""
                INSERT INTO users (username, email, password, role, status, team_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, email, password, "user", "active", team_id))

            # ✅ Get newly created user id
            user_id = cursor.lastrowid

            # ✅ Insert into team_members table
            if team_id:
                cursor.execute("""
                    INSERT INTO team_members (team_id, user_id)
                    VALUES (?, ?)
                """, (team_id, user_id))

            conn.commit()
            flash("Registration successful!", "success")
            return redirect(url_for('login'))

        except sqlite3.IntegrityError:
            flash("Username or Email already exists!", "danger")

    conn.close()
    return render_template('register.html', teams=teams)

# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        if not user:
            flash("User not found!", "danger")
            conn.close()
            return redirect(url_for("login"))

        if user["role"] != "admin" and user["status"] != "active":
            flash("Account inactive!", "danger")
            conn.close()
            return redirect(url_for("login"))

        if not check_password_hash(user["password"], password):
            flash("Wrong password!", "danger")
            conn.close()
            return redirect(url_for("login"))

        # ✅ Update last seen
        conn.execute(
            "UPDATE users SET last_seen = datetime('now') WHERE username=?",
            (username,)
        )
        conn.commit()
        conn.close()

        # ✅ Session
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        session["team_id"] = user["team_id"]

        if user["role"] == "admin":
            return redirect(url_for("chat_section", section="dashboard"))

        return redirect(url_for("chat_section", section="chat"))

    return render_template("login.html")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    if "username" in session:
        conn = get_db()
        conn.execute(
            "UPDATE users SET last_seen = datetime('now') WHERE username=?",
            (session["username"],)
        )
        conn.commit()
        conn.close()

    session.clear()
    return redirect(url_for("login"))


# ================= MAIN =================
@app.route("/chat/<section>", methods=["GET", "POST"])
@login_required
def chat_section(section):
    conn = get_db()
    cursor = conn.cursor()

    selected_user = None   # ✅ ADD THIS LINE (VERY IMPORTANT)

    users = cursor.execute("SELECT * FROM users").fetchall()

    messages = []
    all_users = []
    teams = []
    groups = []
    team_members_map = {}

    total_users = 0
    active_users = 0
    total_teams = 0
    total_groups = 0

    # ===== CHAT =====
    if section == "chat":
     selected_user = request.args.get("user")

    # SEND MESSAGE
    receiver = request.form.get("receiver")  # ✅ define first

    if request.method == "POST":
     message = request.form.get("message")
    file = request.files.get("file")

    if receiver and (message or file):
        # your logic here

     filename = None
     image = None
     voice = None

    # HANDLE FILE UPLOAD
    if file and file.filename != "":
        filename = secure_filename(file.filename)

        upload_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(upload_path)

        ext = filename.lower()

        # DETECT TYPE
        if ext.endswith((".png", ".jpg", ".jpeg", ".gif")):
            image = filename
            filename = None

        elif ext.endswith((".mp3", ".wav", ".ogg")):
            voice = filename
            filename = None

    # INSERT MESSAGE (ALLOW EMPTY TEXT if FILE EXISTS)
    if receiver and (message or file):
        cursor.execute("""
            INSERT INTO messages (sender, receiver, message, file, image, voice)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session["username"],
            receiver,
            message,
            filename,
            image,
            voice
        ))

        conn.commit()   

    # BUILD SIDEBAR USER LIST WITH EXTRA INFO
    users = cursor.execute("""
        SELECT username, last_seen FROM users
        WHERE username != ?
    """, (session["username"],)).fetchall()

    upgraded_users = []

    for user in users:
        uname = user["username"]

        # Last message
        last_msg = cursor.execute("""
            SELECT message FROM messages
            WHERE (sender=? AND receiver=?)
            OR (sender=? AND receiver=?)
            ORDER BY timestamp DESC LIMIT 1
        """, (
            session["username"], uname,
            uname, session["username"]
        )).fetchone()

        # Unread count
        unread = cursor.execute("""
            SELECT COUNT(*) FROM messages
            WHERE sender=? AND receiver=? AND is_read=0
        """, (uname, session["username"])).fetchone()[0]

        # Online status (active within 2 minutes)
        online = False
        if user["last_seen"]:
            last_seen = user["last_seen"]
            online = True  # simple version (always show green if logged once)

        upgraded_users.append({
            "username": uname,
            "last_message": last_msg["message"] if last_msg else "",
            "unread": unread,
            "online": online
        })

    users = upgraded_users

    # LOAD MESSAGES
    if selected_user:
        messages = cursor.execute("""
            SELECT * FROM messages
            WHERE (sender=? AND receiver=?)
            OR (sender=? AND receiver=?)
            ORDER BY timestamp
        """, (
            session["username"], selected_user,
            selected_user, session["username"]
        )).fetchall()

        # MARK AS READ
        cursor.execute("""
            UPDATE messages
            SET is_read=1
            WHERE sender=? AND receiver=?
        """, (selected_user, session["username"]))
        conn.commit()

    # ===== DASHBOARD =====
    if section == "dashboard":
        total_users = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        active_users = cursor.execute("SELECT COUNT(*) FROM users WHERE status='active'").fetchone()[0]
        total_teams = cursor.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
        total_groups = cursor.execute("SELECT COUNT(*) FROM groups").fetchone()[0]

        teams = cursor.execute("SELECT * FROM teams").fetchall()
        groups = cursor.execute("SELECT * FROM groups").fetchall()

    # ===== ADMIN USERS =====
    if section == "admin":
        all_users = cursor.execute("SELECT * FROM users").fetchall()

    # ===== TEAM =====
    if section == "team":
        teams = cursor.execute("SELECT * FROM teams").fetchall()

        for team in teams:
            members = cursor.execute("""
                SELECT users.username FROM team_members
                JOIN users ON users.id = team_members.user_id
                WHERE team_members.team_id=?
            """, (team["id"],)).fetchall()

            team_members_map[team["id"]] = members

    # ===== GROUP =====
    if section == "group":
        groups = cursor.execute("SELECT * FROM groups").fetchall()

    conn.close()

    return render_template(
        "chat.html",
        section=section,
        users=users,
        messages=messages,
        all_users=all_users,
        teams=teams,
        groups=groups,
        total_users=total_users,
        active_users=active_users,
        total_teams=total_teams,
        total_groups=total_groups,
        team_members_map=team_members_map
    )


# ================= ADMIN ACTIONS =================
@app.route("/toggle_user/<int:user_id>")
@login_required
@admin_required
def toggle_user(user_id):
    conn = get_db()
    cursor = conn.cursor()

    user = cursor.execute("SELECT username, status FROM users WHERE id=?", (user_id,)).fetchone()

    if user["username"] == "admin":
        flash("Admin cannot be disabled!", "danger")
        return redirect(url_for("chat_section", section="admin"))

    new_status = "inactive" if user["status"] == "active" else "active"

    cursor.execute("UPDATE users SET status=? WHERE id=?", (new_status, user_id))
    conn.commit()
    conn.close()

    return redirect(url_for("chat_section", section="admin"))


@app.route("/change_role/<int:user_id>")
@login_required
@admin_required
def change_role(user_id):
    conn = get_db()
    cursor = conn.cursor()

    user = cursor.execute("SELECT role FROM users WHERE id=?", (user_id,)).fetchone()
    new_role = "admin" if user["role"] == "user" else "user"

    cursor.execute("UPDATE users SET role=? WHERE id=?", (new_role, user_id))
    conn.commit()
    conn.close()

    return redirect(url_for("chat_section", section="admin"))


@app.route("/delete_user/<int:user_id>")
@login_required
@admin_required
def delete_user(user_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("chat_section", section="admin"))


# ================= TEAM =================
@app.route("/create_team", methods=["POST"])
@login_required
@admin_required
def create_team():
    name = request.form["team_name"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO teams (name) VALUES (?)", (name,))
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
        cursor.execute("INSERT INTO team_members (team_id, user_id) VALUES (?, ?)", (team_id, user_id))

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


# ================= GROUP =================
@app.route("/create_group", methods=["POST"])
@login_required
@admin_required
def create_group():
    name = request.form["group_name"]
    members = request.form.getlist("members")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO groups (name) VALUES (?)", (name,))
    group_id = cursor.lastrowid

    for user_id in members:
        cursor.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)", (group_id, user_id))

    conn.commit()
    conn.close()

    return redirect(url_for("chat_section", section="group"))


@app.route("/delete_group/<int:group_id>")
@login_required
@admin_required
def delete_group(group_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM groups WHERE id=?", (group_id,))
    cursor.execute("DELETE FROM group_members WHERE group_id=?", (group_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("chat_section", section="group"))


# ================= RUN =================
if __name__ == "__main__":
    init_db()
    app.run(debug=True)