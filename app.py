from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import hashlib
import os
import redis
import json
from gevent import monkey
monkey.patch_all()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-12345'

# 🔥 Redis (Render se auto milega)
redis_url = os.environ.get("REDIS_URL")
r = redis.from_url(redis_url, decode_responses=True)

# 🔌 SocketIO (Redis Queue enabled)
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
        return redirect(url_for('index', error="Room does not exist. Please create or join it from the home page."))
        
    saved_password = r.hget(room_key, "password")
    if saved_password and not session.get(f'auth_{room_name}'):
        return redirect(url_for('index', error="You must enter the correct password to join this room!"))

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
        return redirect(url_for('index', error="Room name required!"))

    room_key = f"room:{room_name}"

    # Room exists?
    if not r.exists(room_key):
        password_hash = hashlib.sha256(password.encode()).hexdigest() if password else ""
        r.hset(room_key, mapping={
            "password": password_hash,
            "users": 0
        })
        session[f'auth_{room_name}'] = True
        return redirect(url_for('room', room_name=room_name))

    else:
        room_data = r.hgetall(room_key)
        saved_password = room_data.get("password")

        if saved_password:
            if not password:
                return redirect(url_for('index', error="Password required!"))
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

    # store user session in Redis
    r.hset(f"session:{request.sid}", mapping={
        "room": room,
        "username": username
    })

    # increment user count
    r.hincrby(f"room:{room}", "users", 1)

    send({
        'type': 'system',
        'message': f'{username} joined the room!',
        'username': 'System'
    }, room=room)

    emit('welcome', {'room': room, 'username': username})


@socketio.on('message')
def handle_message(data):
    session_data = r.hgetall(f"session:{request.sid}")

    if session_data:
        room = session_data.get("room")
        username = session_data.get("username")

        msg_payload = {
            'type': 'user',
            'message': data.get('message', ''),
            'username': username
        }
        
        if 'media' in data:
            msg_payload['media'] = data['media']
            msg_payload['media_type'] = data.get('media_type', '')

        send(msg_payload, room=room)


@socketio.on('disconnect')
def handle_disconnect():
    session_data = r.hgetall(f"session:{request.sid}")

    if session_data:
        room = session_data.get("room")
        username = session_data.get("username")

        leave_room(room)

        send({
            'type': 'system',
            'message': f'{username} disconnected.',
            'username': 'System'
        }, room=room)

        # delete session
        r.delete(f"session:{request.sid}")

        # decrement users
        users = r.hincrby(f"room:{room}", "users", -1)

        if users <= 0:
            r.delete(f"room:{room}")


# -------------------- MAIN --------------------

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080)