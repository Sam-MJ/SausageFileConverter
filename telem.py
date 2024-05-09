import requests
import uuid
from PySide6 import QtCore
from dotenv import load_dotenv
import os
import datetime
import json


class SendThread(QtCore.QThread):

    has_internet = QtCore.Signal(bool)

    @QtCore.Slot(str)
    def set_payload(self, payload):
        self.payload = payload

    def run(self):
        database_url = os.getenv("DATABASE_URL")
        print(f"send first payload {self.payload}")
        #
        try:
            requests.post(database_url, json=self.payload, timeout=15)
        except Exception as e:
            print(e)
            self.has_internet.emit(False)


class Telem(QtCore.QObject):

    payload = QtCore.Signal(str)

    def __init__(self, ctrl) -> None:
        super().__init__(parent=None)
        self.ctrl = ctrl
        # data
        self.session_uuid = uuid.uuid4().hex
        self.files_created = 0
        self.files_scanned = 0
        self.session_start = datetime.datetime.now().isoformat()
        self.session_end = datetime.datetime.now().isoformat()

        self.internet_status = True
        # api calls
        load_dotenv(override=True)
        self._send_first_request()

    def _send_first_request(self):

        self.ip_thread = SendThread()
        self.ip_thread.has_internet.connect(self._assign_internet)
        self.payload.connect(self.ip_thread.set_payload)
        pl = self._get_json_payload()
        self.payload.emit(pl)
        self.ip_thread.start()

    def _assign_internet(self, internet_status):
        self.internet_status = internet_status

    def _get_json_payload(self):
        self.files_scanned = self.ctrl["files_scanned"]
        self.files_created = self.ctrl["files_created"]
        print("get files_scanned len")
        self.session_end = datetime.datetime.now().isoformat()

        payload = {
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

        pl = self._get_json_payload()
        database_url = os.getenv("DATABASE_URL")
        r = requests.post(database_url, json=pl, timeout=15)
        print(r)

    @QtCore.Slot(int)
    def on_progress(self):
        """send"""
        self.send_payload()


if __name__ == "__main__":
    pass
