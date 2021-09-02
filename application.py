
from os import access
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO
import urllib.parse
import string 
import random 
from Connection import *
import numpy as np
import cv2
import numpy as np



window_name = 'crop'
size_max_image = 500
debug_mode = False


def get_image_width_height(image):
    image_width = image.shape[1]  # current image's width
    image_height = image.shape[0]  # current image's height
    return image_width, image_height


def calculate_scaled_dimension(scale, image):
    # http://www.pyimagesearch.com/2014/01/20/basic-image-manipulations-in-python-and-opencv-resizing-scaling-rotating-and-cropping/
    image_width, image_height = get_image_width_height(image)
    ratio_of_new_with_to_old = scale / image_width
    dimension = (scale, int(image_height * ratio_of_new_with_to_old))
    return dimension


def rotate_image(image, degree=180):
    # http://www.pyimagesearch.com/2014/01/20/basic-image-manipulations-in-python-and-opencv-resizing-scaling-rotating-and-cropping/
    image_width, image_height = get_image_width_height(image)
    center = (image_width / 2, image_height / 2)
    M = cv2.getRotationMatrix2D(center, degree, 1.0)
    image_rotated = cv2.warpAffine(image, M, (image_width, image_height))
    return image_rotated


def scale_image(image, size):
    image_resized_scaled = cv2.resize(
        image,
        calculate_scaled_dimension(
            size,
            image
        ),
        interpolation=cv2.INTER_AREA
    )
    return image_resized_scaled

def detect_box(image, cropIt=True):
    # https://stackoverflow.com/questions/36982736/how-to-crop-biggest-rectangle-out-of-an-image/36988763
    # Transform colorspace to YUV
    image_yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
    image_y = np.zeros(image_yuv.shape[0:2], np.uint8)
    image_y[:, :] = image_yuv[:, :, 0]

    # Blur to filter high frequency noises
    image_blurred = cv2.GaussianBlur(image_y, (3, 3), 0)
    if (debug_mode):  show_image(image_blurred, window_name)

    # Apply canny edge-detector
    edges = cv2.Canny(image_blurred, 100, 300, apertureSize=3)
    if (debug_mode): show_image(edges, window_name)

    # Find extrem outer contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if (debug_mode):
         #                                      b  g   r
         cv2.drawContours(image, contours, -1, (0, 255, 0), 3)
         show_image(image, window_name)

    # https://stackoverflow.com/questions/37803903/opencv-and-python-for-auto-cropping
    # Remove large countours
    new_contours = []
    for c in contours:
        if cv2.contourArea(c) < 4000000:
            new_contours.append(c)

    # Get overall bounding box
    best_box = [-1, -1, -1, -1]
    for c in new_contours:
        x, y, w, h = cv2.boundingRect(c)
        if best_box[0] < 0:
            best_box = [x, y, x + w, y + h]
        else:
            if x < best_box[0]:
                best_box[0] = x
            if y < best_box[1]:
                best_box[1] = y
            if x + w > best_box[2]:
                best_box[2] = x + w
            if y + h > best_box[3]:
                best_box[3] = y + h

    if (debug_mode):
        cv2.rectangle(image, (best_box[0], best_box[1]), (best_box[2], best_box[3]), (0, 255, 0), 1)
        show_image(image, window_name)

    if (cropIt):
        image = image[best_box[1]:best_box[3], best_box[0]:best_box[2]]
        if (debug_mode): show_image(image, window_name)

    return image


def show_image(image, window_name):
    # Show image
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.imshow(window_name, image)
    image_width, image_height = get_image_width_height(image)
    cv2.resizeWindow(window_name, image_width, image_height)

    # Wait before closing
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def cut_of_top(image, pixel):
    image_width, image_height = get_image_width_height(image)

    # startY, endY, startX, endX coordinates
    new_y = 0+pixel
    image = image[new_y:image_height, 0:image_width]
    return image

def cut_of_bottom(image, pixel):
    image_width, image_height = get_image_width_height(image)

    # startY, endY, startX, endX coordinates
    new_height = image_height-pixel
    image = image[0:new_height, 0:image_width]
    return image

def enhance(infile,outfile):
    image = cv2.imread(infile)

    image = rotate_image(image)
    image = cut_of_bottom(image, 1000)

    image = scale_image(image, size_max_image)
    

    image = detect_box(image, True)

    cv2.imwrite(outfile, image)


app = Flask(__name__, static_url_path='/static')
hostname = '192.168.29.212:5000'

CORS(app)
app.config['SECRET_KEY'] = 'nuha23nansi9qwjjas9qw9'
socketio = SocketIO(app,cors_allowed_origins="*")

# @app.after_request
# def after_request(response):
#   response.headers.add('Access-Control-Allow-Origin', '*')
#   response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
#   response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
#   return response

@app.route('/')
def sessions():
    return "Flask server is running"

@app.route('/viewer')
def viewer():
    return render_template('viewer.html')

@app.route('/scanner')
def scanner():
    return render_template('scanner.html')

def saveImage(imageData):
    response = urllib.request.urlopen(imageData)

    filename=''.join(random.choices(string.ascii_uppercase +
                             string.digits, k = 15))
    file = 'static/assets/raw/'+filename+'.png'
    out_file = 'static/assets/raw/'+filename+'_scanned.png'
    with open(file, 'wb') as f:
        f.write(response.file.read())
    
    enhance(file,out_file)
    return filename+'_scanned'

@app.route('/uploadImage', methods = ['POST'])
# @cross_origin()
def uploadImage():
    jsonObject=request.json
    print(request)
    print(request.__dict__.items())
    print(jsonObject)
    jsonObject=request.get_json(force=True)
    username=jsonObject['username']
    datauri=jsonObject['datauri']
    filename = saveImage(datauri)
    outFilePath = 'static/assets/raw/'+filename+'.png'

    serverPath = 'http://'+hostname+'/'+outFilePath
    # enhance('static/assets/raw/'+filename+'.png',outFilePath)



    viewerId = connections.access_objects(username = username)

    jsonString = '{"id":"'+filename+'","url":"'+serverPath+'","name":"'+filename+'"}'
    print(viewerId)
    socketio.emit('send_image_viewer',jsonString, room=viewerId.viewer_ws_id)

    retData={"message" : "success"}
    return jsonify(retData)

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
    print("Viewer connected")
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
    print("SCANNER IMGAE-------------- FOUND!!")
    image_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 15))
    path = 'static/assets/' + image_name + '.jpeg'
    response = urllib.request.urlopen(data)
    with open(path, 'wb') as f:
        f.write(response.file.read())
    save_path = 'static/assets/' + image_name + '_scanned.jpeg'
    
    scanned_image(path,save_path)
    
    scanner_id = request.sid
    connected_pair = connections.access_objects(scanner_ws_id = scanner_id)
    socketio.emit('send_image_viewer', {'img_url' : save_path} , room=connected_pair.viewer_ws_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
