import face_recognition
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from flask_pymongo import PyMongo
from datetime import datetime
from bson.json_util import dumps
import numpy as np
import random

app = Flask(__name__)
CORS(app)

app.config["MONGO_URI"] = ""
mongo = PyMongo(app)

#load encodings from db
def load_encodings_db():
    user_collection = mongo.db.users

    encodings = []
    names = []
    ids = []

    for x in user_collection.find({}, {"_id": 0, 'id': 1, "name": 1, "encoding": 1}):
        encoding_des = np.fromiter(x['encoding'], dtype=float)
        encodings.append(encoding_des)
        names.append(x['name'])
        ids.append(x['id'])
    
    return encodings, names, ids

#load encodings from array - ONLY USED FOR TESTING PURPOSES
def load_encodings():
    name_encoding = []

    encodings = [
        name_encoding
    ]

    names = [
        "Name"
    ]

    return encodings, names

#compare faces to loaded encodings
def compare_face(file, room):
    image = face_recognition.load_image_file(file)
    image_encoding = face_recognition.face_encodings(image)
    if image_encoding:
        match = face_recognition.compare_faces(known_face_encodings, image_encoding[0])
        if match:
            if True in match:
                first_match_index = match.index(True)
                name = known_face_names[first_match_index]
                ID = known_face_id[first_match_index]
                add_recognition(ID, name, room)
                return ID
    
    name = "Unknown person"
    
    return name

#add faces to database + array
def add_face(file, ID, name):
    image = face_recognition.load_image_file(file)
    image_encoding = face_recognition.face_encodings(image)
    
    if image_encoding:
        known_face_encodings.append(image_encoding[0])
        known_face_names.append(name)
        known_face_id.append(ID)

        encoding = image_encoding[0].tolist()

        user_collection = mongo.db.users
        user_collection.insert_one({'id': ID, 'name' : name, "encoding" : encoding})
        
        print("added " + ID + " to server")
        return ID
    else:
        return "False"

#add recognition to database
def add_recognition(ID, name, room):
    recognition_collection = mongo.db.recognitions #recognitions = new, recognition = test
    recognition_collection.insert_one({'id' : ID, 'name' : name, "time" : datetime.utcnow(), "room" : room})

@app.route('/recognitions', methods=['GET'])
def get_recognitions():
    if request.method == 'GET':
        recognition_collection = mongo.db.recognitions
        result = recognition_collection.find({}, {"_id": 0, "id": 1, "name": 1, "time": 1, "room": 1})
        return dumps(result)

@app.route('/', methods=['POST'])
def base_func():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        room = request.form['room']

        if file.filename == '':
            return redirect(request.url)

        if file:
            return compare_face(file, room)

@app.route('/upload', methods=['POST'])
def new_face():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']
        name = request.form['name']

        if file.filename == '':
            return redirect(request.url)

        if file:
            return add_face(file, file.filename, name)

@app.route('/')
def index():
    return "<h1>Server here!</h1>"

known_face_encodings, known_face_names, known_face_id = load_encodings_db()

if __name__ == '__main__':
    app.run(threaded=True, port=5000)