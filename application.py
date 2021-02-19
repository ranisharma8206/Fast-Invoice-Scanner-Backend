
from os import access
from flask import Flask, render_template, request
from flask_socketio import SocketIO
import urllib.parse
import string 
import random 
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
def scanner_key_pressed():
    print('Key presssed....')
    viewer_id = request.sid
    connected_pair = connections.access_objects(viewer_ws_id = viewer_id)
    socketio.emit('send_scanner_key_pressed_signal', room=connected_pair.scanner_ws_id)

@socketio.on('scanner_get_image')
def scanner_get_image(data):
    image_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 15))
    path = 'assets/images/' + image_name + '.png'
    response = urllib.request.urlopen(data['data'])
    with open(path, 'wb') as f:
        f.write(response.file.read())
    scanner_id = request.sid
    connected_pair = connections.access_objects(scanner_ws_id = scanner_id)
    socketio.emit('send_image_viewer', {'data' : path} , room=connected_pair.viewer_ws_id)

if __name__ == '__main__':
    socketio.run(app, debug=True)