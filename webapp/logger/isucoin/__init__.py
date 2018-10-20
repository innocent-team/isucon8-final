from __future__ import annotations

import os, sys
sys.path.append(os.path.dirname(__file__) + "/vendor") 
import contextlib
import datetime
import json
import time
import flask

app = flask.Flask(__name__)

def _json_default(v):
    if isinstance(v, datetime.datetime): return v.strftime("%Y-%m-%dT%H:%M:%S+09:00") 
    to_json = getattr(v, "to_json")
    if to_json:
        return to_json()

    raise TypeError(f"Unknown type for json_dumps. {v!r} (type: {type(v)})")


def json_dumps(data, **kwargs):
    return json.dumps(data, default=_json_default, **kwargs)


def jsonify(*args, **kwargs):
    if args and kwargs:
        raise TypeError("jsonify() behavior undefined when passed both args and kwargs")
    if len(args) == 1:
        data = args[0]
    else:
        data = args or kwargs

    return app.response_class(
        json_dumps(data, indent=None, separators=(",", ":")).encode(),
        mimetype="application/json; charset=utf-8",
    )

import json
import time
import urllib.parse

import requests
import threading

import redis


LOG_ENDPOINT = "log_endpoint"
LOG_APPID = "log_appid"

# Global settings
_redisconn = None
_redispool = None


def _redis():
    # NOTE: get_dbconn() is not thread safe.  Don't use threaded server.
    global _redisconn
    global _redispool

    if _redisconn is None:
        _redispool = redis.ConnectionPool(
            host='localhost',
            port=6379,
            db=0,
        )
        _redisconn = redis.StrictRedis(
            connection_pool=_redispool
        )

    return _redisconn

def get_setting(k: str) -> str:
    r = _redis().get(k)
    print(r, k)
    if r is None : raise Exception("[Error] No setting of " + k)
    return r.decode('utf-8')

def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t

queue = []
def send_bulk():
    endpoint = get_setting(LOG_ENDPOINT)
    appid = get_setting(LOG_APPID)
    url = urllib.parse.urljoin(endpoint, "/send_bulk")
    body = json.dumps(queue)
    print("SEND BULK size: " + str(len(body)))
    queue.clear()
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + appid,
    }
    res = requests.post(url, data=body, headers=headers)
    res.raise_for_status()

set_interval(send_bulk, 2)

@app.route("/send", methods=("POST",))
def send():
    queue.append(flask.request.json)
    return jsonify({})

@app.route("/initialize", methods=("POST",))
def initialize():
    print("Initalize Logger")
    queue.clear()
    return jsonify({})

