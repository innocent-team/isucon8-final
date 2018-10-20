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

app = flask.Flask(__name__, static_url_path="", static_folder=public)
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


def error_json(code: int, msg):
    resp = jsonify(code=code, err=str(msg))
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.status_code = code
    return resp


@app.errorhandler(Exception)
def errohandler(err):
    app.logger.exception("FAIL")
    return error_json(500, err)


@app.before_request
def before_request():
    user_id = flask.session.get("user_id")
    if user_id is None:
        flask.g.current_user = None
        return

    user = model.get_user_by_id(get_dbconn(), user_id)
    if user is None:
        flask.session.clear()
        return error_json(404, "セッションが切断されました")

    flask.g.current_user = user


@contextlib.contextmanager
def transaction():
    conn = get_dbconn()
    conn.begin()
    try:
        yield conn
    except:
        conn.rollback()
        raise
    else:
        conn.commit()

@app.route("/initialize", methods=("POST",))
def initialize():
    with transaction() as db:
        model.init_benchmark(db)

    for server in ['isucon1', 'isucon2', 'isucon4']:
        print(f"send request to {server}")
        urllib.request.urlopen(f"http://{server}:5000/initialize_redis").read()
    
    return jsonify({})
