"""
MI300 to InfluxDB

An application to periodically read statistics from Bosswerk MI300 and similar micro inverters and pipe them to InfluxDB.

Author: GiantMolecularCloud
Version: 0.1

This script uses environment variables for authentification and settings:
INVERTER_IP     IP address of the Bosswerk MI300 (or compatible) inverter
INVERTER_USER   user to access the inverter web interface
INVERTER_PASSWD password to access the inverter web interface
INFLUX_IP       IP address of the machine InfluxDB is running on, default: 127.0.0.1
INFLUX_PORT     port to connect to InfluxDB, default: 8086
INFLUX_USER     user to access the InfluxDB database, default: root
INFLUX_PASSWD   password to access the InfluxDB database, default: root
DB_NAME         Database to write the measurements to, default: solarpower
TIMEZONE        Timezone of assume for the time, default: Europe/Berlin
SAMPLE_TIME     time to wait before getting the next sample, default: 60
DEBUG           Wether to enable debug messages, default: False
"""

import logging
import os
import time

from influx import Influx
from mi300 import MI300


logging.basicConfig(level=logging.INFO, format="%(asctime)s -  %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("main")

# inverter settings
INVERTER_IP = os.getenv("INVERTER_IP")
INVERTER_USER = os.getenv("INVERTER_USER")
INVERTER_PASSWD = os.getenv("INVERTER_PASSWD")

# influxdb settings
INFLUX_IP = os.getenv("INFLUX_IP", default="127.0.0.1")
INFLUX_PORT = int(os.getenv("INFLUX_PORT", default="8086"))
INFLUX_USER = os.getenv("INFLUX_USER", default="root")
INFLUX_PASSWD = os.getenv("INFLUX_PASSWD", default="root")
DB_NAME = os.getenv("DB_NAME", default="solarpower")

# other settings
SAMPLE_TIME = int(os.getenv("SAMPLE_TIME", default=60))
DEBUG = bool(os.getenv("DEBUG", default="False"))


if DEBUG:
    logger.setLevel("DEBUG")


def main():

    mi300 = MI300(INVERTER_IP, INVERTER_USER, INVERTER_PASSWD, DEBUG)
    influx = Influx(INFLUX_IP, INFLUX_PORT, INFLUX_USER, INFLUX_PASSWD, DB_NAME, DEBUG)

    try:
        while True:
            try:

                if mi300.is_reachable:
                    mi300.read_data()
                    influx.write(mi300.influx_data)
                else:
                    logger.debug("Inverter is off-line.")

            except Exception as e:
                logger.error(e)

            finally:
                time.sleep(SAMPLE_TIME)

    except KeyboardInterrupt:
        logger.warning("Program stopped by keyboard interrupt [CTRL_C] by user.")


if __name__ == "__main__":
    main()
