from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-12345'
socketio = SocketIO(app, cors_allowed_origins="*")

# Database initialize
def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_name TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def room_exists(room_name):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('SELECT * FROM rooms WHERE room_name = ?', (room_name,))
    room = c.fetchone()
    conn.close()
    return room

def create_room(room_name, password=None):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    if password:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        c.execute('INSERT INTO rooms (room_name, password_hash) VALUES (?, ?)',
                  (room_name, password_hash))
    else:
        c.execute('INSERT INTO rooms (room_name) VALUES (?)', (room_name,))
    conn.commit()
    conn.close()

def get_room_password_hash(room_name):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('SELECT password_hash FROM rooms WHERE room_name = ?', (room_name,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/room/<room_name>')
def room(room_name):
    username = session.get('username')
    return render_template('index.html', room_name=room_name, username=username)

@app.route('/join_room', methods=['POST'])
def join_room_route():
    room_name = request.form.get('room_name', '').strip()
    password = request.form.get('password', '').strip()
    username = request.form.get('username', '').strip()
    
    if username:
        session['username'] = username
    
    if not room_name:
        return "Room name required!", 400
    
    room = room_exists(room_name)
    
    if not room:
        create_room(room_name, password if password else None)
        return redirect(url_for('room', room_name=room_name))
    else:
        room_password_hash = get_room_password_hash(room_name)
        
        if room_password_hash:
            if not password:
                return "Password required!", 401
            entered_hash = hashlib.sha256(password.encode()).hexdigest()
            if entered_hash != room_password_hash:
                return "Wrong password!", 401
        
        return redirect(url_for('room', room_name=room_name))

# SocketIO Events
@socketio.on('join')
def handle_join(data):
    room = data['room']
    username = data.get('username', 'Anonymous')
    join_room(room)
    session['room'] = room
    session['username'] = username
    send({
        'type': 'system',
        'message': f'{username} joined the room!',
        'username': 'System'
    }, room=room)
    emit('welcome', {'room': room, 'username': username})

@socketio.on('message')
def handle_message(data):
    room = session.get('room')
    username = session.get('username', 'Anonymous')
    if room:
        send({
            'type': 'user',
            'message': data['message'],
            'username': username
        }, room=room)

@socketio.on('disconnect')
def handle_disconnect():
    room = session.get('room')
    username = session.get('username', 'Anonymous')
    if room:
        leave_room(room)
        send({
            'type': 'system',
            'message': f'{username} disconnected.',
            'username': 'System'
        }, room=room)

if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True, host='0.0.0.0', port=8000)