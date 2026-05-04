from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import hashlib
import os
import redis
import json
from gevent import monkey

# Fast handling ke liye monkey patching
monkey.patch_all()

app = Flask(__name__)

# SECURITY FIX: Ab key code mein nahi, server ki settings mein hogi
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-very-secret-local-key')

# 🔥 Redis Setup (Environment se URL lega)
redis_url = os.environ.get("REDIS_URL")
if not redis_url:
    # Agar local pe chala rahe ho toh default connection
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
else:
    r = redis.from_url(redis_url, decode_responses=True)

# 🔌 SocketIO Setup
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    message_queue=redis_url,
    async_mode='gevent'
)

# -------------------- ROUTES --------------------

@app.route('/')
def index():
    error = request.args.get('error')
    return render_template('index.html', error=error)

@app.route('/room/<room_name>')
def room(room_name):
    room_key = f"room:{room_name}"
    
    if not r.exists(room_key):
        return redirect(url_for('index', error="Room does not exist!"))
        
    saved_password = r.hget(room_key, "password")
    if saved_password and not session.get(f'auth_{room_name}'):
        return redirect(url_for('index', error="Password required!"))

    username = session.get('username', 'Anonymous')
    return render_template('index.html', room_name=room_name, username=username)

@app.route('/join_room', methods=['POST'])
def join_room_route():
    room_name = request.form.get('room_name', '').strip()
    password = request.form.get('password', '').strip()
    username = request.form.get('username', '').strip()

    if username:
        session['username'] = username
    if not room_name:
        return redirect(url_for('index', error="Room name required!"))

    room_key = f"room:{room_name}"

    if not r.exists(room_key):
        # Naya Room Banana
        password_hash = hashlib.sha256(password.encode()).hexdigest() if password else ""
        r.hset(room_key, mapping={"password": password_hash, "users": 0})
        session[f'auth_{room_name}'] = True
        return redirect(url_for('room', room_name=room_name))
    else:
        # Purane Room mein Entry
        saved_password = r.hget(room_key, "password")
        if saved_password:
            entered_hash = hashlib.sha256(password.encode()).hexdigest()
            if entered_hash != saved_password:
                return redirect(url_for('index', error="Wrong password!"))

        session[f'auth_{room_name}'] = True
        return redirect(url_for('room', room_name=room_name))

# -------------------- SOCKET EVENTS --------------------

@socketio.on('join')
def handle_join(data):
    room = data['room']
    username = data.get('username', 'Anonymous')
    join_room(room)
    r.hset(f"session:{request.sid}", mapping={"room": room, "username": username})
    r.hincrby(f"room:{room}", "users", 1)
    
    r.hset(f"room_users:{room}", request.sid, username)
    current_users = list(r.hvals(f"room_users:{room}"))
    emit('update_users', {'users': current_users}, room=room)
    
    send({'type': 'system', 'message': f'{username} joined!', 'username': 'System'}, room=room)

@socketio.on('message')
def handle_message(data):
    session_data = r.hgetall(f"session:{request.sid}")
    if session_data:
        msg_payload = {
            'type': 'user',
            'message': data.get('message', ''),
            'username': session_data.get("username")
        }
        if 'media' in data:
            msg_payload.update({'media': data['media'], 'media_type': data.get('media_type', '')})
        send(msg_payload, room=session_data.get("room"))

@socketio.on('disconnect')
def handle_disconnect():
    sid_key = f"session:{request.sid}"
    session_data = r.hgetall(sid_key)
    if session_data:
        room = session_data.get("room")
        send({'type': 'system', 'message': f'{session_data.get("username")} left the room.', 'username': 'System'}, room=room)
        r.delete(sid_key)
        
        r.hdel(f"room_users:{room}", request.sid)
        current_users = list(r.hvals(f"room_users:{room}"))
        emit('update_users', {'users': current_users}, room=room)
        
        users = r.hincrby(f"room:{room}", "users", -1)
        if users <= 0:
            r.delete(f"room:{room}")
            r.delete(f"room_users:{room}")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080)