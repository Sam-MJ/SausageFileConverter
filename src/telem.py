import requests
import uuid
from PySide6 import QtCore
from dotenv import load_dotenv
import os
import datetime
import json
import time


class SendThread(QtCore.QThread):

    has_internet = QtCore.Signal(bool)

    def __init__(self, payload):
        super().__init__()
        self.payload = payload

    def run(self):
        # self.payload = payload

        self.database_url = os.getenv("DATABASE_URL")

        try:
            requests.post(self.database_url, json=self.payload, timeout=15)
        except Exception as e:
            self.has_internet.emit(False)
        # print(f"send first payload {self.payload}")


class Telem(QtCore.QObject):

    def __init__(self, ctrl) -> None:
        super().__init__(parent=None)
        self.ctrl = ctrl
        # data and defaults
        self.telem_version = 1
        self.session_uuid = uuid.uuid4().hex
        self.my_mac = hex(uuid.getnode())
        self.files_created = 0
        self.files_scanned = 0
        self.session_start = datetime.datetime.now().isoformat()
        self.session_end = datetime.datetime.now().isoformat()

        self.internet_status = True
        # method calls
        load_dotenv(override=True)
        self._send_first_request()

    def _send_first_request(self):
        """create a thread that can use the run method to fetch ip on creation, the ip is then added to the request payload."""
        payload = self._get_json_payload()
        self.first_send_thread = SendThread(payload)

        # send first payload and see if there is a successful internet connection
        self.first_send_thread.has_internet.connect(self._assign_internet)

        self.first_send_thread.start()

    def _assign_internet(self, internet_status):
        self.internet_status = internet_status

    def _get_json_payload(self):
        """populate dictionary with instance variables and then convert to json"""

        self.files_scanned = self.ctrl["files_scanned"]
        self.files_created = self.ctrl["files_created"]

        self.session_end = datetime.datetime.now().isoformat()

        payload = {
            "telem_version": self.telem_version,
            "mac_address": self.my_mac,
            "session_id": self.session_uuid,
            "files_created": self.files_created,
            "files_scanned": self.files_scanned,
            "session_start": self.session_start,
            "session_end": self.session_end,
        }
        json_payload = json.dumps(payload)
        return json_payload

    def send_payload(self):

        if self.internet_status is False:
            return None
            # this also returns None if the server isn't running.

        pl = self._get_json_payload()
        database_url = os.getenv("DATABASE_URL")
        r = requests.post(database_url, json=pl, timeout=15)
        # print(r)

    @QtCore.Slot(int)
    def on_progress(self):
        """When a file has finished, the payload is sent again to update values."""
        self.send_payload()


if __name__ == "__main__":
    pass
