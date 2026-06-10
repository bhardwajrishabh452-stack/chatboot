# 💬 Time Team Chat Application with Admin Dashboard

A real-time company communication platform built with **Flask**, **Flask-SocketIO**, and **SQLite**. The application enables employees to communicate through private and group chats while providing administrators with tools to manage users and departments.

---

## 🚀 Features

### 🔐 Authentication
- User Registration
- Secure Login
- Password Hashing
- Session Management
- Logout Functionality

### 👥 Role-Based Access
- Admin User
- Employee User
- Automatic Admin Creation for the First Registered User

### 💬 Private Messaging
- One-to-one chat
- Real-time message delivery
- Message history storage
- Persistent chat records

### 🏢 Group Chat
- Department-based communication
- Real-time group messaging
- Group membership management
- Chat history

### 👑 Admin Panel
- Create groups
- View users
- Manage departments
- Monitor communication

### 📡 Real-Time Communication
- Flask-SocketIO integration
- Instant message broadcasting
- Room-based messaging
- Live updates

### 💾 Database Support
- SQLite database
- User management
- Group management
- Private messages
- Group messages

---

# 🛠 Tech Stack

| Technology | Purpose |
|-----------|----------|
| Python | Backend |
| Flask | Web Framework |
| Flask-SocketIO | Real-time communication |
| SQLite | Database |
| HTML | Frontend |
| CSS | Styling |
| JavaScript | Client-side interaction |
| Werkzeug Security | Password hashing |

---

# 📂 Project Structure

```
chatboot-main/
│
├── app.py
├── database.db
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── chat.html
│   ├── group.html
│   ├── dm.html
│   ├── admin.html
│   └── monitor.html
│
├── static/
│   ├── style.css
│   └── style.js
│
├── uploads/
│
└── instance/
```

---

# ⚙️ Installation

## Clone the repository

```bash
git clone https://github.com/yourusername/company-chat.git

cd company-chat
```

---

## Create Virtual Environment

### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

### Linux/Mac

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install flask flask-socketio werkzeug
```

---

## Run the Application

```bash
python app.py
```

Server starts at:

```
http://127.0.0.1:5050
```

---

# 🗄 Database Schema

The application automatically creates the required tables:

## Users

- id
- username
- email
- password
- role

## Groups

- id
- name
- created_by

## Group Members

- id
- group_name
- username

## Group Messages

- id
- group_name
- sender
- message
- timestamp

## Private Messages

- id
- sender
- receiver
- message
- timestamp

---

# 👨‍💼 Admin Features

The first registered user automatically becomes an Admin.

Admin can:

✅ Create groups

✅ View users

✅ Access admin dashboard

✅ Monitor chats

---

# 👨‍💻 User Features

Users can:

- Register
- Login
- Send private messages
- Participate in group chats
- View previous conversations
- Logout securely

---

# 📡 Socket Events

## Join Room

```javascript
join
```

## Send Group Message

```javascript
send_message
```

## Receive Group Message

```javascript
receive_message
```

## Send Private Message

```javascript
private_message
```

## Receive Private Message

```javascript
receive_private_message
```

---

# 🔒 Security Features

- Password hashing
- Session authentication
- Role-based authorization
- Protected routes
- User validation

---

# 📷 Application Pages

- Login Page
- Registration Page
- Home Dashboard
- Private Chat
- Group Chat
- Admin Panel
- Chat Monitoring Dashboard

---

# 🚧 Future Improvements

- File sharing
- Image sharing
- Voice messages
- Video calls
- Typing indicators
- Online/offline status
- Read receipts
- Message search
- User profile pictures
- Group management enhancements
- Email verification
- Password reset
- Docker deployment
- PostgreSQL/MySQL support

---

# 🤝 Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Push the branch.
5. Open a Pull Request.

---

# 📄 License

This project is developed for educational and learning purposes. You may modify and extend it according to your requirements.

---

# 👨‍💻 Author

**Rishabh Bhardwaj**

Python Developer | Full Stack Developer

If you found this project useful, consider giving it a ⭐ on GitHub.
