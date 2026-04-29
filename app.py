from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import hashlib
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-12345'

# 🔥 IMPORTANT: Redis URL from Render
redis_url = os.environ.get("REDIS_URL")

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    message_queue=redis_url,   # ✅ FIX
    async_mode='eventlet'
)

# Temporary rooms (still okay with 1 worker OR Redis sync)
rooms = {}

connected_users = {}

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

    if room_name not in rooms:
        password_hash = hashlib.sha256(password.encode()).hexdigest() if password else None
        rooms[room_name] = {
            'password_hash': password_hash,
            'users': 0
        }
        return redirect(url_for('room', room_name=room_name))
    else:
        room_password_hash = rooms[room_name]['password_hash']

        if room_password_hash:
            if not password:
                return "Password required!", 401
            entered_hash = hashlib.sha256(password.encode()).hexdigest()
            if entered_hash != room_password_hash:
                return "Wrong password!", 401

        return redirect(url_for('room', room_name=room_name))


# 🔌 SOCKET EVENTS

@socketio.on('join')
def handle_join(data):
    room = data['room']
    username = data.get('username', 'Anonymous')

    join_room(room)

    connected_users[request.sid] = {
        'room': room,
        'username': username
    }

    if room not in rooms:
        rooms[room] = {'password_hash': None, 'users': 0}

    rooms[room]['users'] += 1

    send({
        'type': 'system',
        'message': f'{username} joined the room!',
        'username': 'System'
    }, room=room)

    emit('welcome', {'room': room, 'username': username})


@socketio.on('message')
def handle_message(data):
    user_info = connected_users.get(request.sid)

    if user_info:
        room = user_info['room']
        username = user_info['username']

        send({
            'type': 'user',
            'message': data['message'],
            'username': username
        }, room=room)


@socketio.on('disconnect')
def handle_disconnect():
    user_info = connected_users.get(request.sid)

    if user_info:
        room = user_info['room']
        username = user_info['username']

        leave_room(room)

        send({
            'type': 'system',
            'message': f'{username} disconnected.',
            'username': 'System'
        }, room=room)

        del connected_users[request.sid]

        if room in rooms:
            rooms[room]['users'] -= 1
            if rooms[room]['users'] <= 0:
                del rooms[room]


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)