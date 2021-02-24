
from os import access
from flask import Flask, render_template, request
from flask_cors import CORS
from flask_socketio import SocketIO
import urllib.parse
import string 
import random 
from Connection import *

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'nuha23nansi9qwjjas9qw9'
socketio = SocketIO(app,cors_allowed_origins="*")



@app.route('/')
def sessions():
    return "Flask server is running"

@app.route('/viewer')
def viewer():
    return render_template('viewer.html')

@app.route('/scanner')
def scanner():
    return render_template('scanner.html')

#--------------------------------------------------------------------------------------------------------------
#----------------------------------------------Socket IO Definations
#--------------------------------------------------------------------------------------------------------------

@socketio.on('connect')
def connect():
    print("connected succesfully..................")

@socketio.on('disconnect')
def disconnect():
    disconnecting_socket_id = request.sid

    # disconnecting socket can either be a viewer or scanner, both needs to handled differently.

    disconnected_viewer = connections.access_objects(viewer_ws_id = disconnecting_socket_id) 
    if(disconnected_viewer != None):
        #disconnecting socket is viewer, connection data needs to removed.
        connections.remove_connection(disconnected_viewer.connection_pair_id) #removes the connection from list
        print("Viewer disconnected")

    disconnected_scanner = connections.access_objects(scanner_ws_id = disconnecting_socket_id)
    if(disconnected_scanner != None):
        #disconnecting socket is scanner, mapping of scanner->viewer needs to be reset.
        disconnected_scanner.disconnect_scanner() #remove the mapping
        print("Scanner disconnected")


# schema for data
# {
#     'username': <string>
# }
@socketio.on('viewer_connect')
def viewer_connect(data):
    viewer_id = request.sid
    connections.add_connection(data, viewer_id) #TODO: Check if add_connection returned success.


# schema for data
# {
#     'connected_viewers_username_list': [<string>,...]
# }
@socketio.on('scanner_found')
def scanner_found():
    scanner_id = request.sid
    connected_viewers_username = []
    for c in connections.connection_pair_list:
        connected_viewers_username.append(c.username)
    print(connected_viewers_username)
    socketio.emit('send_viewers_list', {'connected_viewers_username_list': connected_viewers_username}, room=scanner_id)


# schema for data
# {
#     'username' :<string>
# }
@socketio.on('scanner_connect')
def scanner_connect(data):
    scanner_id = request.sid
    viewer = connections.access_objects(username = data)
    if(viewer != None):
        viewer.scanner_ws_id = scanner_id



# schema for data
# {
# }
@socketio.on('viewer_key_press')
def viewer_key_press():
    print('Key presssed....')
    viewer_id = request.sid
    connected_pair = connections.access_objects(viewer_ws_id = viewer_id)
    socketio.emit('send_key_press_signal', room=connected_pair.scanner_ws_id)


#schema for scanner_get_image :
# {
#     datauri: string encoding of image
# }


@socketio.on('scanner_get_image')
def scanner_get_image(data):
    image_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 15))
    path = 'assets/images/' + image_name + '.jpeg'
    response = urllib.request.urlopen(data)
    with open(path, 'wb') as f:
        f.write(response.file.read())
    scanner_id = request.sid
    connected_pair = connections.access_objects(scanner_ws_id = scanner_id)
    socketio.emit('send_image_viewer', {'img_url' : path} , room=connected_pair.viewer_ws_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0')