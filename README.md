# MI300 to Influx

An application to periodically read statistics from Bosswerk MI300 and similar micro inverters and pipe them to InfluxDB.
Inverters such as Bosswerk MI300, Bosswerk MI600 and Deye Sun-600G3 should be compatible but this is tested on an MI300 only.

All 23 available statistics are forwarded. The most important are probably "power_current", "yield_today" and "yield_total".

## Local execution

Install influxdb:  
`pip install -r docker/requirements.txt`

Set enviroment variables:

```
export INVERTER_IP='192.168.178.1'
export INVERTER_USER='12345678'
export INVERTER_PASSWD='87654321'
export INFLUX_IP='192.168.178.2'
export INFLUX_USER='user'
export INFLUX_PASSWD='passwd'
```

Run the app:  
`python src/run.py`

## docker

Build the image:  
`docker build -t mi300influx:0.1 -f docker/Dockerfile .`

Run the container:

```
docker run \
-e INVERTER_IP='192.168.178.1' \
-e INVERTER_USER='12345678' \
-e INVERTER_PASSWD='87654321' \
-e INFLUX_IP='192.168.178.2' \
-e INFLUX_USER='user' \
-e INFLUX_PASSWD='passwd' \
mi300influx:0.1 mi300influx
```

## Options

The connection details for the inverter are set through env variables.
If InfluxDB does not run with default values, its connection details can also be set through env variables.
Further options are also available.
When no variables are given, the following defaults are assumed:

| env variable    | default      | explanation                                               |
| --------------- | ------------ | --------------------------------------------------------- |
| INVERTER_IP     | no default   | IP address of the Bosswerk MI300 (or compatible) inverter |
| INVERTER_USER   | no default   | user to access the inverter web interface                 |
| INVERTER_PASSWD | no default   | password to access the inverter web interface             |
| INFLUX_IP       | 127.0.0.1    | IP address of the machine InfluxDB is running on          |
| INFLUX_PORT     | 8086         | port to connect to InfluxDB                               |
| INFLUX_USER     | 'root'       | user to access the InfluxDB database                      |
| INFLUX_PASSWD   | 'root'       | password to access the InfluxDB database                  |
| DB_NAME         | 'solarpower' | Database to write the measurements to                     |
| SAMPLE_TIME     | 60           | time in seconds to wait before getting the next sample    |
| DEBUG           | False        | Wether to enable debug messages                           |
