from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import hashlib
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-12345'
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory storage for temporary rooms
# Structure: { 'room_name': { 'password_hash': '...', 'users': 0 } }
rooms = {}

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
        # Create new temporary room
        password_hash = hashlib.sha256(password.encode()).hexdigest() if password else None
        rooms[room_name] = {
            'password_hash': password_hash,
            'users': 0
        }
        return redirect(url_for('room', room_name=room_name))
    else:
        # Room exists, check password
        room_password_hash = rooms[room_name]['password_hash']
        
        if room_password_hash:
            if not password:
                return "Password required!", 401
            entered_hash = hashlib.sha256(password.encode()).hexdigest()
            if entered_hash != room_password_hash:
                return "Wrong password!", 401
        
        return redirect(url_for('room', room_name=room_name))

# Dictionary to map WebSocket session IDs to their room and username
# Structure: { 'socket_id': {'room': 'room_name', 'username': 'user_name'} }
connected_users = {}

# SocketIO Events
@socketio.on('join')
def handle_join(data):
    room = data['room']
    username = data.get('username', 'Anonymous')
    join_room(room)
    
    # Reliably track user by their specific SocketIO connection ID
    connected_users[request.sid] = {
        'room': room,
        'username': username
    }
    
    # In case the server restarted but client reconnected
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
    # Lookup the user's room and name using their connection ID
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
        
        # Remove from connected tracking
        del connected_users[request.sid]
        
        if room in rooms:
            rooms[room]['users'] -= 1
            if rooms[room]['users'] <= 0:
                del rooms[room]

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=8000)