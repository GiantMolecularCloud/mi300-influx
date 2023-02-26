import logging
import subprocess
from datetime import datetime
from typing import Any, Dict, Optional

import requests
from requests.exceptions import Timeout


class MI300:
    def __init__(
        self,
        ip: str,
        user: str,
        password: str,
        debug: bool = False,
    ) -> None:
        self.logger = logging.getLogger("MI300")
        self.ip = ip
        self.user = user
        self.passwd = password
        self.influx_data: Optional[list] = None
        self.DEBUG = debug

        if self.DEBUG:
            self.logger.setLevel("DEBUG")

    def is_reachable(self) -> None:
        """
        Ping the inverter to test if it is online.
        The inverter shuts down when the panel output is too low to save power.
        """

        command = ["ping", "-c", "1", self.ip]
        self.is_reachable = subprocess.call(command) == 0

        return self.is_reachable

    def query(self) -> None:
        """
        Connect to the inverter and read data from it.
        """

        self.get_html()
        self.parse_html()

    def read_data(self) -> None:
        """
        Read data from the inverter. Retry if no data is returned.
        Occasionally only empty fields are returned by the inverter.
        """

        tries = 0
        while tries < 5:
            self.query()
            if self.influx_data[0]["fields"]["yield_total"] is not None:
                break

    def get_html(self) -> None:
        """
        Connect to the inverter and obtain the web interface.
        """

        self.time = datetime.utcnow()
        try:
            request = requests.get(
                f"http://{self.ip}/status.html",
                verify=False,
                auth=(self.user, self.passwd),
                timeout=2,
            )
        except Timeout:
            self.logger.debug("Request to inverter web interface timed out.")
            self.request_status_code = None
            self.request_reason = None
            self.request_elapsed = None
            self.request_html = None
        else:
            self.request_status_code = request.status_code
            self.request_reason = request.reason
            self.request_elapsed = request.elapsed
            if request.status_code == 200:
                self.request_html = request.text
            else:
                self.request_html = None
                self.logger.debug(f"Request failed. Status code: {request.status_code}. Reason: {request.reason}")
        finally:
            request.close()

    def _value_or_none(self, value: Any, dtype: type = str) -> Optional[int | float | bool]:
        """
        Return None if the value is an empty string or otherwise cast to the given type.
        """

        if dtype == str:
            return value.strip() if value else None
        if dtype == int:
            return int(value) if value.isdigit() else None
        if dtype == float:
            try:
                return float(value)
            except ValueError:
                return None
        if dtype == bool:
            return bool(int(value)) if value else None
        else:
            raise TypeError(f"Type '{dtype}' is not implemented.")

    def parse_html(self) -> None:
        """
        Decode the web interface html and parse the values of interest.
        """

        if self.request_status_code is None:
            self.influx_data = None
        else:
            if self.request_status_code != 200:
                measure_names = [
                    "inverter_serial_number",
                    "firmware_main",
                    "firmware_slave",
                    "inverter_model",
                    "power_rated",
                    "power_current",
                    "yield_today",
                    "yield_total",
                    "alerts",
                    "last_updated",
                    "device_serial_number",
                    "firmware_version",
                    "WiFi_mode",
                    "AP_SSID",
                    "AP_IP",
                    "AP_mac",
                    "STA_SSID",
                    "STA_signal_quality",
                    "STA_IP",
                    "STA_mac",
                    "remote_server_A_connected",
                    "remote_server_B_connected",
                    "remote_server_C_connected",
                ]
                measures = {k: None for k in measure_names}
                measures["request_status_code"] = self.request_status_code
                measures["request_reason"] = self.request_reason
                measures["request_elapsed"] = self.request_elapsed.total_seconds()

            else:
                html = self.request_html.split("\r\n")
                js_vars = [
                    line.strip("var ").strip(";")
                    for line in html
                    if line.startswith("var web") or line.startswith("var cover") or line.startswith("var status")
                ]
                js_vars = [v.split(" = ") for v in js_vars]
                js_vars = {v[0]: v[1].strip('"') for v in js_vars}
                measures = {
                    "request_status_code": self.request_status_code,
                    "request_reason": self.request_reason,
                    "request_elapsed": self.request_elapsed.total_seconds(),
                    "inverter_serial_number": self._value_or_none(js_vars["webdata_sn"]),
                    "firmware_main": self._value_or_none(js_vars["webdata_msvn"]),
                    "firmware_slave": self._value_or_none(js_vars["webdata_ssvn"]),
                    "inverter_model": self._value_or_none(js_vars["webdata_pv_type"]),
                    "power_rated": self._value_or_none(js_vars["webdata_rate_p"], dtype=int),
                    "power_current": self._value_or_none(js_vars["webdata_now_p"], dtype=int),
                    "yield_today": self._value_or_none(js_vars["webdata_today_e"], dtype=float),
                    "yield_total": self._value_or_none(js_vars["webdata_total_e"], dtype=float),
                    "alerts": self._value_or_none(js_vars["webdata_alarm"]),
                    "last_updated": self._value_or_none(js_vars["webdata_utime"], dtype=int),
                    "device_serial_number": self._value_or_none(js_vars["cover_mid"]),
                    "firmware_version": self._value_or_none(js_vars["cover_ver"]),
                    "WiFi_mode": self._value_or_none(js_vars["cover_wmode"]),
                    "AP_SSID": self._value_or_none(js_vars["cover_ap_ssid"]),
                    "AP_IP": self._value_or_none(js_vars["cover_ap_ip"]),
                    "AP_mac": self._value_or_none(js_vars["cover_ap_mac"]),
                    "STA_SSID": self._value_or_none(js_vars["cover_sta_ssid"]),
                    "STA_signal_quality": self._value_or_none(js_vars["cover_sta_rssi"].strip("%"), dtype=int),
                    "STA_IP": self._value_or_none(js_vars["cover_sta_ip"]),
                    "STA_mac": self._value_or_none(js_vars["cover_sta_mac"]),
                    "remote_server_A_connected": self._value_or_none(js_vars["status_a"], dtype=bool),
                    "remote_server_B_connected": self._value_or_none(js_vars["status_b"], dtype=bool),
                    "remote_server_C_connected": self._value_or_none(js_vars["status_c"], dtype=bool),
                }

            self.influx_data = [
                {
                    "measurement": measures["inverter_serial_number"],
                    "time": self.time,
                    "fields": measures,
                }
            ]
