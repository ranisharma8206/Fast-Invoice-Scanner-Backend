
from os import access
from flask import Flask, render_template, request
from flask_socketio import SocketIO
from Connection import *

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def sessions():
    return render_template('session.html')

@app.route('/viewer')
def viewer():
    return render_template('viewer.html')

@app.route('/scanner')
def scanner():
    return render_template('scanner.html')

@socketio.on('connect')
def test_connect():
    print("connected succesfully..................")

@socketio.on('disconnect')
def test_disconnect():
    disconnecting_socket_id = request.sid
    disconnected_viewer = connections.access_objects(viewer_ws_id = disconnecting_socket_id)
    if(disconnected_viewer != None):
        connections.remove_connection(disconnected_viewer.connection_pair_id)

    disconnected_scanner = connections.access_objects(scanner_ws_id = disconnecting_socket_id)
    if(disconnected_scanner != None):
        disconnected_scanner.disconnect_scanner()
        print("Scanner disconnected...")

@socketio.on('viewer_connect')
def viewer_connect(data):
    viewer_id = request.sid
    connections.add_connection(data["data"], viewer_id)

@socketio.on('scanner_found')
def scanner_found():
    scanner_id = request.sid
    connected_viewers_username = []
    for c in connections.connection_pair_list:
        connected_viewers_username.append(c.username)
    socketio.emit('send_viewers_list', {'data': connected_viewers_username}, room=scanner_id)

@socketio.on('scanner_connect')
def add_scanner(data):
    scanner_id = request.sid
    viewer = connections.access_objects(username = data["data"])
    if(viewer != None):
        viewer.scanner_ws_id = scanner_id


@socketio.on('viewer_key_pressed')
def scanner_key_pressed(data):
    print('Message: ' + data["data"])

@socketio.on('scanner_get_image')
def scanner_get_image(data):
    print('Message: ' + data["data"])

if __name__ == '__main__':
    socketio.run(app, debug=True)