from datetime import datetime
from flask import json, request, Response, _app_ctx_stack
from files import JWE, database
from functools import wraps
d = database

def check_auth(username, password):
    return username == 'filesystem' and password == config.basic
def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'No Access for you.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


from flask_cors import CORS, cross_origin

CORS(app, resources=r'/api/*')

@app.route("/api/", methods=['POST', 'GET'])
@requires_auth
def api():
    data = {'status': 'fail'}
    try:
        # d.db.create_all()
        # d.db.session.commit()
        data['status'] = 'success'
    except Exception as e:
        data['message'] = str(e)
    finally:
        return json.dumps(data)

@app.route("/api/start/", methods=['POST', 'GET'])
@JWE.requires_auth
def start():
    data = {'status': 'fail'}
    cu = _app_ctx_stack.top.current_user
    try:
        data['departments'] = [d.asdict(x) for x in d.Users.query.filter_by(id=cu['id']).first().departments]
        data['status'] = 'success'
    except Exception as e:
        data['message'] = str(e)
    finally:
        return json.dumps(data)


@app.route("/api/users/<action>/", methods=['POST', 'GET'])
@JWE.requires_auth
def admin_users(action):
    data = {'status': 'success'}
    cu = _app_ctx_stack.top.current_user
    if cu['userlevel'] < 9:
        raise Exception("Permission Denied")
    try:
        if action == 'all':
            data['users'] = [user.getAddressCard() for user in d.Users.query.order_by(d.Users.accountname.asc()).all()]
        elif action == 'get' and 'id' in request.json:
            data['user'] = d.asdict(d.Users.query.get(request.json['id']))
        elif action == 'getEmail' and 'id' in request.json:
            data['user'] = d.asdict(d.Users.query.get(request.json['id']))
            dMail = d.UsersEmails.query.filter_by(user_id=request.json['id']).first()
            if data['user']:
                if dMail:
                    data['email'] = d.asdict(dMail)
                else:
                    data['email'] = {}
            else:
                raise Exception('No user found')
        elif action == "emailAccounts" and set(['id', 'data']).issubset(request.json):
            emailAccount = d.UsersEmails.query.filter_by(user_id=request.json['id']).first()
            if emailAccount:
                d.db.session.delete(emailAccount)
            email = d.UsersEmails(**request.json['data'])
            d.db.session.add(email)
            d.db.session.commit()
        elif action == "update" and set(['id', 'data']).issubset(request.json) and 'id' not in request.json['data']:
            query = d.Users.query.filter_by(id=request.json['id'])
            query.update(dict(request.json['data']))
            d.db.session.flush()
            data['user'] = d.asdict(query.first())
            d.db.session.commit()
        else:
            raise Exception("No Action")
    except Exception as e:
        data['status'] = 'fail'
        data['message'] = str(e)
    finally:
        return json.dumps(data)