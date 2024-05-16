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
    ip = QtCore.Signal(str)

    @QtCore.Slot(str)
    def send_payload(self, payload):
        self.payload = payload
        database_url = os.getenv("DATABASE_URL")
        # database_url = "http://www.soundspruce.com//sausagefileconverter-transactions"

        try:
            requests.post(database_url, json=self.payload, timeout=15)
        except Exception as e:
            self.has_internet.emit(False)

        print(f"send first payload {self.payload}")

    def run(self):
        time.sleep(3)
        ip_address = requests.get("https://api.ipify.org", timeout=15).text
        self.ip.emit(ip_address)


class Telem(QtCore.QObject):

    payload = QtCore.Signal(str)

    def __init__(self, ctrl) -> None:
        super().__init__(parent=None)
        self.ctrl = ctrl
        # data
        self.telem_version = 1
        self.session_uuid = uuid.uuid4().hex
        self.my_mac = hex(uuid.getnode())
        self.my_ip = None
        self.files_created = 0
        self.files_scanned = 0
        self.session_start = datetime.datetime.now().isoformat()
        self.session_end = datetime.datetime.now().isoformat()

        self.internet_status = True
        # api calls
        load_dotenv(override=True)
        self._send_first_request()

    def _send_first_request(self):

        self.first_send_thread = SendThread()
        self.first_send_thread.has_internet.connect(self._assign_internet)
        self.first_send_thread.ip.connect(self._assign_ip_to_payload)
        self.payload.connect(self.first_send_thread.send_payload)
        self.first_send_thread.start()

    def _assign_internet(self, internet_status):
        self.internet_status = internet_status

    def _assign_ip_to_payload(self, ip):
        self.my_ip = ip
        pl = self._get_json_payload()
        self.payload.emit(pl)

    def _get_json_payload(self):
        self.files_scanned = self.ctrl["files_scanned"]
        self.files_created = self.ctrl["files_created"]

        self.session_end = datetime.datetime.now().isoformat()

        payload = {
            "telem_version": self.telem_version,
            "ip_address": self.my_ip,
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
