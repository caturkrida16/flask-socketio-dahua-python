# TASK BERFORE RUN THIS PROGRAM
"""
1. You need to set environment variable for:
1.1 HOST (IP Camera address / domain)
1.2 USERNAME (IP Camera username)
1.3 PASSWORD (IP Camera passowrd)
1.4 CALLBACK_URL (IP / Domain callback your server)
1.5 CLIENT_SECRET (Path your Oauth2 Credentials JSON from GCP)
1.6 SECRET (Secrer for your application)
"""



### >>><<< ###
# Packages
## System
import json
import os

## PIP
from flask import Flask, jsonify, request, render_template, Response, session, abort, redirect
import cv2
from flask_socketio import SocketIO
from sensecam_control import onvif_control
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import simplejpeg
import pathlib
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests



### >>><<< ###
# Initialization
## Environment Variable
host = os.getenv("HOST")
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
callback_url = os.getenv("CALLBACK_URL")
client_secret = os.getenv("CLIENT_SECRET")
secret = os.getenv("SECRET")

## Core   
app = Flask(__name__)
app.config["SECRET_KEY"] = secret
socketio = SocketIO(app, cors_allowed_origins='*')
cam = onvif_control.CameraControl(host, username, password)
cam.camera_start()

## Google Login
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
read_ci = open("client_secret.json")
read_ci_data = json.load(read_ci)
GOOGLE_CLIENT_ID = read_ci_data["web"]["client_id"]
read_ci.close()
flow = Flow.from_client_secrets_file(client_secrets_file=client_secret, scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"], redirect_uri=callback_url)

## Dahua HTTP API (Specify)
http_api = "http://" + host + "/cgi-bin"
reboot = "/magicBox.cgi?action=reboot"
get_system_info = "/magicBox.cgi?action=getSystemInfo"



### >>><<< ###
# Core
## REST API
### index Stream from Website
@app.route("/", methods=["GET"])
def index():
    return render_template('index.html')
  
### MJPEG Stream    
@app.route("/stream", methods=["GET"])
def stream():
    # Connect to RTSP Stream
    rtsp_stream = cv2.VideoCapture("rtsp://" + username + ":" + password + "@" + host + ":554/cam/realmonitor?channel=1&subtype=1")
    return Response(cam_frames(rtsp_stream), mimetype='multipart/x-mixed-replace; boundary=frame')

### Login
@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)
  
### Logout  
@app.route("/logout")
def logout():
    session.clear()
    return "Logout"

### Callback
@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)
    id_info = id_token.verify_oauth2_token(id_token=credentials._id_token, request=token_request, audience=GOOGLE_CLIENT_ID)
    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    id_info["id_token"] = credentials._id_token
    
    return id_info

## SocketIO
### PTZ Control
@socketio.on("ptz_control")
def ptz_control(json):
    from google.auth.transport import requests
    try:
        id_info = id_token.verify_oauth2_token(json["id_token"], requests.Request(), GOOGLE_CLIENT_ID)
        ptz_cam(json["direction"]) # Move Camera
        cam.stop_move() # And stop it
    except:
        print("False ID Token / Direction")
    
## Function   
### Generate camera frames
def cam_frames(rtsp):
    while True:
        success, frame = rtsp.read()
        if not success:
            break
            
        else:
            buffer = simplejpeg.encode_jpeg(frame, 85, colorspace="BGR", fastdct=True)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer + b'\r\n')
                   
### ONVIF PTZ Control
def ptz_cam(direction):
    # Up
    if (direction == "Up"):
        cam.continuous_move(0, 1, 0)

    # Left
    elif (direction == "Left"):
        cam.continuous_move(-1, 0, 0)

    # Down
    elif (direction == "Down"):
        cam.continuous_move(0, -1, 0)

    # Right
    elif (direction == "Right"):
        cam.continuous_move(1, 0, 0)

    # Zoom In
    elif (direction == "ZoomIn"):
        cam.continuous_move(0, 0, 1)

    # Zoom Out
    elif (direction == "ZoomOut"):
        cam.continuous_move(0, 0, -1)

### >>><<< ###
# APP Run
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080, debug=True)

    

### >>><<< ###
# Archive
"""
### Move the Camera View 
@app.route("/ptz_move", methods=["POST"])
@auth.login_required
def ptz_move():
    data = request.json
    try:
        if (data["action"] == "start" or data["action"] == "stop"):
            if (data["direction"] == "Up" or data["direction"] == "Down" or data["direction"] == "Left" or data["direction"] == "Right" or data["direction"] == "LeftUp" or data["direction"] == "RightUp" or data["direction"] == "LeftDown" or data["direction"] == "RightDown"):
                if (data["speed"] >= 1 and data["speed"] <= 8):
                    response = api_auth(http_api + "/ptz.cgi?action=" + data["action"] + "&channel=1&code=" + data["direction"] + "&arg1=0&arg2=" + str(data["speed"]) + "&arg3=0")
                    return response, 200
                else:
                    return "Invalid PTZ Speed", 400
            else:
                return "Invalid PTZ Direction", 400
        else:
            return "Invalid PTZ Action", 400
    except:
        return "Your JSON is error", 400

### Dahua API Authentication
def api_auth(url):
    response = requests.get(url)
    auth_type = response.headers["WWW-Authenticate"].split(" ")[0]
    if (auth_type.lower() == "basic"):
        response = requests.get(url, auth=HTTPBasicAuth(username, password))
        return response.text
        
    elif (auth_type.lower() == "digest"):
        response = requests.get(url, auth=HTTPDigestAuth(username, password))
        return response.text

    else:
        print("Unknown authentication type!")
"""
