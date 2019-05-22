import jwe
import os
from _datetime import datetime

from functools import wraps
from flask import Flask, request, jsonify, _app_ctx_stack, json
from flask_cors import cross_origin
from filesystem import config

try:
    client_id = "FILESYSTEM API"
    client_secret = config.secret
except IOError:
    env = os.environ

# Format error response and append status code.
def handle_error(error, status_code):
    resp = jsonify(error)
    resp.status_code = status_code
    return resp

def getEncode():
    return jwe.kdf(str.encode(config.secret), str.encode(config.salt))


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', None)
        if not auth:
            return handle_error({'message': 'authorization_header_missing',
                                'description':
                                    'Authorization header is expected'}, 401)
        parts = auth.split()

        if parts[0].lower() != 'bearer':
            return handle_error({'message': 'invalid_header',
                                'description':
                                    'Authorization header must start with'
                                    'Bearer'}, 401)
        elif len(parts) == 1:
            return handle_error({'message': 'invalid_header',
                                'description': 'Token not found'}, 401)
        elif len(parts) > 2:
            return handle_error({'message': 'invalid_header',
                                'description': 'Authorization header must be'
                                 'Bearer + \s + token'}, 401)

        token = parts[1]
        try:
            payload = jwe.decrypt(
                token.encode("utf-8"),
                getEncode()
            )
            dPayLoad = json.loads(payload.decode("utf-8"))
            if not datetime.strptime(dPayLoad['expires'], "%Y-%m-%d %H:%M:%S.%f") > datetime.now():
                raise Exception("token expired")
            if 'accountname' not in dPayLoad:
                raise Exception("Invalid Token")
            # if 'userlevel' not in dPayLoad or dPayLoad['userlevel'] >= 5:
            #     raise Exception("Status Pending")
        except Exception as e:
            return handle_error({'message': str(e),
                                'description': 'Unable to parse authentication : '+str(e)+ ''
                                 ' token.'}, 400)

        _app_ctx_stack.top.current_user = dPayLoad
        return f(*args, **kwargs)

    return decorated

