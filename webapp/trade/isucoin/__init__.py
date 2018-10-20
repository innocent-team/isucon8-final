from __future__ import annotations

import os, sys

sys.path.append(os.path.dirname(__file__) + "/vendor")

import contextlib
import datetime
import json
import time
import flask
import MySQLdb
import urllib.request

from dataclasses import dataclass, asdict
from . import model


# port   = os.environ.get("ISU_APP_PORT", "5000")
dbhost = os.environ.get("ISU_DB_HOST", "127.0.0.1")
dbport = os.environ.get("ISU_DB_PORT", "3306")
dbuser = os.environ.get("ISU_DB_USER", "root")
dbpass = os.environ.get("ISU_DB_PASSWORD", "")
dbname = os.environ.get("ISU_DB_NAME", "isucoin")
public = os.environ.get("ISU_PUBLIC_DIR", "public")

app = flask.Flask(__name__)
app.secret_key = "tonymoris"

# ISUCON用初期データの基準時間です
# この時間以降のデータはinitializeで削除されます
base_time = datetime.datetime(2018, 10, 16, 10, 0, 0)

_dbconn = None


def get_dbconn():
    # NOTE: get_dbconn() is not thread safe.  Don't use threaded server.
    global _dbconn

    if _dbconn is None:
        _dbconn = MySQLdb.connect(
            host=dbhost,
            port=int(dbport),
            user=dbuser,
            password=dbpass,
            database=dbname,
            charset="utf8mb4",
            autocommit=True,
        )

    return _dbconn


def _json_default(v):
    if isinstance(v, datetime.datetime):
        return v.strftime("%Y-%m-%dT%H:%M:%S+09:00")

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


import threading

def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t

queue = []
def seek_queue():
    if len(queue) > 0:
        queue.pop()
        start_trading()

set_interval(seek_queue, 0.1)

def start_trading():
    print("Start Trading")
    db = get_dbconn()
    try:
         model.trades.run_trade(db) 
    except Exception:  # トレードに失敗してもエラーにはしない
        print("Trade Error")

@app.route("/initialize", methods=("POST",))
def initialize():
    queue.clear()
    return jsonify({})

@app.route("/trade", methods=("POST",))
def trade():
    queue.append(True)
    return jsonify({})
