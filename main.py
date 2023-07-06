# TASK BERFORE RUN THIS PROGRAM
"""
1. You need to set environment variable HOST, USERNAME, and PASSWORD with IP Camera credentials
"""



### >>><<< ###
# Packages
## System
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import json
import os
import requests

## PIP
from flask import Flask, jsonify, request, render_template, Response
import cv2
from flask_socketio import SocketIO
from sensecam_control import onvif_control



### >>><<< ###
# Initialization
## Environment Variable
host = os.getenv("HOST")
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")

## Core
app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, cors_allowed_origins='*')
cam = onvif_control.CameraControl(host, username, password) # Initialize the ONVIF
cam.camera_start()

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
    
## SocketIO
### PTZ Control from ONVIF
@socketio.on("ptz_control")
def ptz_control(json):
    print(json)
    ptz_cam(json["direction"]) # Move Camera
    cam.stop_move() # And stop it

## Function
### Generate camera frames
def cam_frames(rtsp):
    while True:
        success, frame = rtsp.read()
        if not success:
            break
            
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                   
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
        """
