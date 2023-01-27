# flask imports
import time
import urllib.request
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import uuid  # for public id
from werkzeug.security import generate_password_hash, check_password_hash
# imports for PyJWT authentication
import jwt
from datetime import datetime, timedelta
from functools import wraps
from databaseHelper import DatabaseHelper
import requests

# Schedule Library imported
import schedule
import time

db = DatabaseHelper()
# creates Flask object
app = Flask(__name__)
# configuration
# NEVER HARDCODE YOUR CONFIGURATION IN YOUR CODE
# INSTEAD CREATE A .env FILE AND STORE IN IT
app.config['SECRET_KEY'] = 'your secret key'
# database name
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True


# creates SQLALCHEMY object
# db = SQLAlchemy(app)


# Database ORMs
# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     public_id = db.Column(db.String(50), unique=True)
#     name = db.Column(db.String(100))
#     email = db.Column(db.String(70), unique=True)
#     password = db.Column(db.String(80))


# decorator for verifying the JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # jwt is passed in the request header
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        # return 401 if token is not passed
        if not token:
            return jsonify({'message': 'Token is missing !!'}), 401

        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = db.search_user('user_name', data['user_name'])
            # current_user = User.query \
            #     .filter_by(public_id=data['public_id']) \
            #     .first()
        except:
            return jsonify({
                'message': 'Token is invalid !!'
            }), 401
        # returns the current logged in users contex to the routes
        return f(current_user, *args, **kwargs)

    return decorated


#
# User Database Route
# this route sends back list of users
@app.route('/user', methods=['GET'])
@token_required
def get_all_users(current_user):
    # querying the database
    # for all the entries in it
    # users = User.query.all()
    users = db.search_all('users')
    # converting the query objects
    # to list of jsons
    output = []
    for user in users:
        # appending the user data json
        # to the response list
        output.append({
            'public_id': user.public_id,
            'name': user.name,
            'email': user.email
        })

    return jsonify({'users': output})


# route for logging user in
@app.route('/login', methods=['POST'])
def login():
    # creates dictionary of form data
    auth = request.form

    if not auth.get('password'):
        # returns 401 if password is missing
        return make_response(
            'Could not verify',
            401,
            {'WWW-Authenticate': 'Basic realm ="Login required !!"'}
        )

    # user = User.query \
    #     .filter_by(email=auth.get('email')) \
    #     .first()
    user = db.search_user('user_name', auth.get('name'))

    if not user:
        # returns 401 if user does not exist
        return make_response(
            'Could not verify',
            401,
            {'WWW-Authenticate': 'Basic realm ="User does not exist !!"'}
        )

    if check_password_hash(user.get("password"), auth.get('password')):
        # generates the JWT Token
        token = jwt.encode({
            'user_name': user.get("user_name"),
            'exp': datetime.utcnow() + timedelta(minutes=30)
        }, app.config['SECRET_KEY'])

        return make_response(jsonify({'token': token.decode('UTF-8')}), 201)
    # returns 403 if password is wrong
    return make_response(
        'Could not verify',
        403,
        {'WWW-Authenticate': 'Basic realm ="Wrong Password !!"'}
    )


# signup route
@app.route('/signup', methods=['POST'])
def signup():
    # creates a dictionary of the form data
    data = request.form

    # gets name, email and password
    name = data.get('name')
    password = data.get('password')

    # checking for existing user
    user = db.search_user('user_name', name)
    if not user:
        # database ORM object
        db.add_user(name, generate_password_hash(password))

        return make_response('Successfully registered.', 201)
    else:
        # returns 202 if user already exists
        return make_response('User already exists. Please Log in.', 202)


@app.route('/url', methods=['POST', 'GET'])
@token_required
def add_url(current_user):
    if request.method == 'POST':
        data = request.form
        url = data.get('url')
        threshold = data.get('threshold')
        user_id = current_user['id']
        db.add_url(user_id, url, threshold)
        return make_response(f"url '{url}' added", 200)

    elif request.method == 'GET':
        user_id = current_user['id']
        user_urls = db.search_user_urls(user_id)
        urls = {'urls': [x['url'] for x in user_urls]}
        return jsonify(urls)


@app.route('/urls/stats', methods=['GET'])
@token_required
def get_stats(current_user):
    user_id = current_user['id']
    return jsonify(urls_stats(user_id))


@app.route('/urls/alerts', methods=['GET'])
@token_required
def get_alerts(current_user):
    user_id = current_user['id']
    urls = db.search_user_urls(user_id)
    result = []
    for item in urls:
        url_id = item.get('url_id')
        stats = db.select_request_stats(url_id)
        for stat in stats:
            if stat['status_code'] == 800:
                result.append({
                    'url': item.get('url'),
                    'alert': 'above threshold'
                })
    return jsonify(result)


def check_url(url):
    url = "http://" + url
    payload = ""
    response = requests.request("GET", url, data=payload)
    return response.status_code
    # url = "http://" + url
    # try:
    #     return urllib.request.urlopen(url).getcode()
    # except:
    #     return 0  # if request can't be sent


def urls_stats(user_id):
    urls = db.search_user_urls(user_id)
    result = []
    for item in urls:
        url_id = item.get('url_id')
        stats = db.select_request_stats(url_id)
        result.append({
            'url': item.get('url'),
            'stats': stats
        })
    return result


def send_requests():
    urls_data = db.get_urls_data()
    for item in urls_data:
        print("new item")
        status_code = check_url(item.get('url'))
        print("status code:", status_code)
        # if request fails
        if status_code not in range(200, 300):
            threshold, failed = db.get_threshold_failed(item.get("id"))
            # if failed requests is lower than the threshold
            if failed < threshold:
                db.update_failed_times(item.get("id"))
            else:
                status_code = 800  # means alert

        db.insert_to_requests(item.get('id'), status_code)


if __name__ == "__main__":
    # schedule.every(1).minutes.do(send_requests)
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
    app.run(debug=True)
