from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app)

# Modelo para armazenar mensagens
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)

# Inicializar o banco de dados
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat/<chat_id>')
def chat(chat_id):
    return render_template('chat.html', chat_id=chat_id)

@app.route('/messages/<chat_id>')
def get_messages(chat_id):
    messages = Message.query.filter_by(chat_id=chat_id).all()
    return jsonify([{'username': msg.username, 'message': msg.message} for msg in messages])

@socketio.on('send_message')
def handle_send_message(data):
    chat_id = data['chat_id']
    message = data['message']
    username = data['username']

    # Salvar a mensagem no banco de dados
    new_message = Message(chat_id=chat_id, username=username, message=message)
    db.session.add(new_message)
    db.session.commit()

    # Emitir a mensagem para todos na sala
    emit('receive_message', {'chat_id': chat_id, 'username': username, 'message': message}, room=chat_id)

@socketio.on('join')
def handle_join(data):
    chat_id = data['chat_id']
    username = data['username']
    join_room(chat_id)
    emit('user_joined', {'username': username}, room=chat_id)

@socketio.on('leave')
def handle_leave(data):
    chat_id = data['chat_id']
    username = data['username']
    leave_room(chat_id)
    emit('user_left', {'username': username}, room=chat_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)