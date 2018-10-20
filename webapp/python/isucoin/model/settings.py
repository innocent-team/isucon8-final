from __future__ import annotations

import isubank
import isulogger
import redis


BANK_ENDPOINT = "bank_endpoint"
BANK_APPID = "bank_appid"
LOG_ENDPOINT = "log_endpoint"
LOG_APPID = "log_appid"

# Global settings
_setting = dict()
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


def set_setting(k: str, v: str):
    _redis().set(k, v)
    _setting[k] = v


def get_setting(k: str) -> str:
    if k not in _setting:
        _setting[k] = _redis().get(k)
    return _setting[k]


def get_isubank():
    endpoint = get_setting(BANK_ENDPOINT)
    appid = get_setting(BANK_APPID)
    return isubank.IsuBank(endpoint, appid)


def get_logger():
    endpoint = get_setting(LOG_ENDPOINT)
    appid = get_setting(LOG_APPID)
    return isulogger.IsuLogger(endpoint, appid)


def send_log(tag, v):
    logger = get_logger()
    logger.send(tag, v)
