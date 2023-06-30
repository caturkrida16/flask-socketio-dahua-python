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
import flask_httpauth
from werkzeug.security import generate_password_hash, check_password_hash
import cv2



### >>><<< ###
# Intialization
## System
app = Flask(__name__)
auth = flask_httpauth.HTTPBasicAuth()
host = os.getenv("HOST")
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")

## Dahua HTTP API (Specify)
http_api = "http://" + host + "/cgi-bin"
rtsp_api = "rtsp://" + host + ":554/cam/realmonitor?channel=1&subtype=1"
reboot = "/magicBox.cgi?action=reboot"
get_system_info = "/magicBox.cgi?action=getSystemInfo"

# Users
users = {
    "admin": generate_password_hash("admin")
}



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
    rtsp_stream = cv2.VideoCapture(rtsp_api)
    return Response(cam_frames(rtsp_stream), mimetype='multipart/x-mixed-replace; boundary=frame')

### Move the Camera View 
@app.route("/ptz_move", methods=["POST"])
@auth.login_required
def ptz_move():
    data = request.json
    try:
    if (data["action"] == "start" or data["action"] == "stop"):
        if (data["direction"] == "Up" or data["direction"] == "Down" or data["direction"] == "Left" or data["direction"] == "Right" or data["direction"] == "LeftUp" or data["direction"] == "RightUp" or data["direction"] == "LeftDown" or data["direction"] == "RightDown"):
            if (data["speed"] >= 1 and data["speed"] <= 8):
                response = api_auth(http_api + "/ptz.cgi?action=" + data["action"] + "&channel=0&code=" + data["direction"] + "&arg1=" + str(data["speed"]) + "&arg2=" + str(data["speed"]) + "arg3=0")
                return response, 200
            else:
                return "Invalid PTZ Speed", 400
        else:
            return "Invalid PTZ Direction", 400
    else:
        return "Invalid PTZ Action", 400
    except:
        return "Your JSON is error", 400
    
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
        
### Auth Verify Password
@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username



### >>><<< ###
# APP Run
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True, threaded=True)