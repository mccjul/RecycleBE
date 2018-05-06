import json
import re
from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from random import randint
from shapely.geometry import shape, Point
from watson_developer_cloud import VisualRecognitionV3, WatsonApiException
import geocoder

app = Flask(__name__)
visual_recognition = VisualRecognitionV3('2018-03-19', api_key='fd4da8fef4a085a68316075de318b7183d8cc9ad')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:pass@127.0.0.1:3306/recycle'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class electronics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=False, nullable=True)
    notes = db.Column(db.String, unique=False, nullable=True)
    fullAddress = db.Column(db.String, unique=False, nullable=True)
    city = db.Column(db.String, unique=False, nullable=True)
    province = db.Column(db.String, unique=False, nullable=True)
    postalCode = db.Column(db.String, unique=False, nullable=True)
    lat = db.Column(db.String, unique=False, nullable=True)
    lon = db.Column(db.String, unique=False, nullable=True)

    @property
    def serialize(self):
        """Return object data in easily serialized format"""
        return {
            'name': self.name,
            'notes': self.notes,
            'fullAddress': self.fullAddress,
            'city': self.city,
            'province': self.province,
            'postalCode': self.postalCode
        }

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route("/api", methods=['POST'])
def query():
    if request.method == 'POST':
        rec_type = what_is_that(request.files['file'])
        if request.args.get('test'):
            rec_type = int(request.args['test'])

        if rec_type == 0:
            try:

                # lat, lon = str(request.form.get('geo')).replace(" ", "").split(",")
                return get_bac(request.form.get('geo'))
            except ValueError:
                return "need valid lat-lon in geo"

        elif rec_type == 1:
            try:
                return get_garbage(request.form.get('geo'))
            except ValueError:
                return "need valid lat-lon in geo"
        elif rec_type == 2:
            return get_elec(request.form.get('geo'))
        else:
            return str(what_is_that(request.files['file']))
            # abort(500)


def what_is_that(pic):
    # visual_recognition
    res = visual_recognition.classify(pic)
    stuff = [x['class'] for x in res['images'][0]['classifiers'][0]['classes']]
    print(stuff)
    
    bac = set(['bottle', 'can'])
    electric = set(['electronics'])

    if bac.intersection(set(stuff)):
        return 0
    elif electric.intersection(set(stuff)):
        return 2
    else:
        return 1


def get_elec(data):
    isPostal = re.search('[a-zA-Z]', data)
    if isPostal:
        # give lat and lon
        clean = data.replace(" ", "")
        res = electronics.query.filter(
            electronics.postalCode.contains(' '.join([clean[i:i + 3] for i in range(0, len(clean), 3)]).strip())).all()
        return jsonify({
            'type': 'Electronic',
            'NearestDropOff': [
                {'name': item.name, 'address': item.fullAddress, 'Point': {'lon': str(item.lat), 'lat': str(item.lon)}}
                for item in res
            ]
        })
    else:
        g = geocoder.google(data)
        clean = g.postal.replace(" ", "")
        res = electronics.query.filter(
            electronics.postalCode.contains(' '.join([clean[i:i + 3] for i in range(0, len(clean), 3)]).strip())).all()
        return jsonify({
            'type': 'Electronic',
            'NearestDropOff': [
                {'name': item.name, 'address': item.fullAddress, 'Point': {'lon': str(item.lat), 'lat': str(item.lon)}}
                for item in res
            ]
        })

def get_bac(data):
    isPostal = re.search('[a-zA-Z]', data)
    if isPostal:
        g = geocoder.google(data)
        lon, lat = g.latlng
        lat = float(lat)
        lon = float(lon)
    else:
        lon, lat = str(data).replace(" ", "").split(",")
        lat = float(lat)
        lon = float(lon)
    with open('./recycle.geojson') as f:
        js = json.load(f)
    # construct point based on lon/lat returned by geocoder
    # -73.562253, 45.495579
    point = Point(lat, lon)
    # check each polygon to see if it contains the point
    for feature in js['features']:
        polygon = shape(feature['geometry'])
        if polygon.contains(point):
            properties = feature['properties']
            properties['type'] = 'bac'
            return jsonify(properties)
    return jsonify({
        'type': 'bac',
        'municipalite': 'NONE',
        'jour': 'NONE',
        'frequence': 'NONE',
        'info': 'NONE'
    })

def get_garbage(data):
    isPostal = re.search('[a-zA-Z]', data)
    if isPostal:
        g = geocoder.google(data)
        lon, lat = g.latlng
        lat = float(lat)
        lon = float(lon)
    else:
        lon, lat = str(data).replace(" ", "").split(",")
        lat = float(lat)
        lon = float(lon)
    with open('./ordures.geojson') as f:
        js = json.load(f)
    # construct point based on lon/lat returned by geocoder
    # -73.562253, 45.495579
    point = Point(lat, lon)
    # check each polygon to see if it contains the point
    for feature in js['features']:
        polygon = shape(feature['geometry'])
        if polygon.contains(point):
            properties = feature['properties']
            properties['type'] = 'ordures'
            return jsonify(properties)
    return jsonify({
        'type': 'ordures',
        'municipalite': 'NONE',
        'jour': 'NONE',
        'frequence': 'NONE',
        'info': 'NONE'
    })

if __name__ == '__main__':
    app.run(debug=True)
