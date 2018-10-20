"""
ISULOG client
"""
from __future__ import annotations

import json
import time
import urllib.parse

import requests

LOG_QUEUE_SIZE = 100

class IsuLogger:
    def __init__(self, endpoint, appID):
        self.endpoint = endpoint
        self.appID = appID
        self.queue = []

    def send(self, tag, data):
        self.queue.append({
            "tag": tag,
            "time": time.strftime("%Y-%m-%dT%H:%M:%S+09:00"),
            "data": data,
        })
        if len(self.queue) >= LOG_QUEUE_SIZE:
            self.send_bulk
    
    def send_bulk(self):
        self._request(
            "/send_bulk", self.queue
        )
        self.queue = []
        

    def _request(self, path, data):
        url = urllib.parse.urljoin(self.endpoint, path)
        body = json.dumps(data)
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.appID,
        }

        res = requests.post(url, data=body, headers=headers)
        res.raise_for_status()
