from __future__ import annotations

import isubank
import isulogger


BANK_ENDPOINT = "bank_endpoint"
BANK_APPID = "bank_appid"
LOG_ENDPOINT = "log_endpoint"
LOG_APPID = "log_appid"

# Global settings
_setting = dict()


def set_setting(k: str, v: str):
    _setting[k] = v


def get_setting(k: str) -> str:
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
