import logging
from typing import Any, Dict

import influxdb.exceptions as inexc
from influxdb import InfluxDBClient


class Influx:
    def __init__(self, ip: str, port: int, user: str, password: str, db_name: str, debug: bool = False) -> None:

        self.logger = logging.getLogger("Influx")
        self.client = InfluxDBClient(host=ip, port=port, username=user, password=password)
        self.db_name = db_name
        self.DEBUG = debug

        if self.DEBUG:
            self.logger.setLevel("DEBUG")

        # create new database if necessary
        if not self.db_name in [db["name"] for db in self.client.get_list_database()]:
            self.client.create_database(self.db_name)
            self.logger.info(f"Created new database {self.db_name} because it did not exist yet.")

        # select current database
        self.client.switch_database(self.db_name)

    def write(self, data: Dict[str, Any]) -> None:
        """
        Write the data to the database.

        Parameters
        ----------
        data : Dict[str, Any]
            Data dictionary in the form
            {'measurement: ..., 'time': ..., fields: {...}}

        Raises
        ------
        ConnectionError
            Raised if the client cannot be reached.
        """
        try:
            self.logger.debug(f"Writing points: {data}")
            iresponse = self.client.write_points(data)
            self.logger.debug(f"InfuxDB response: {iresponse}")
            if not iresponse:
                raise ConnectionError("Sending data to database failed.", iresponse)
        except ConnectionError as e:
            self.logger.error("Connection Error.\n", e)
        except inexc.InfluxDBServerError as e:
            self.logger.error("Sending data to database failed due to timeout.\n", e)
        except Exception as e:
            self.logger.error("Encountered unknown error.\n", e)
