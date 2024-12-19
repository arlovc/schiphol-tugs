#!/usr/bin/env python3
"""

Sample client for Flightradar24 position feed.

The client allows testing connectivity to the position feed,
but requires changes for production data consumption.

The code was developed and tested under Python 3.9.1.

List of things to consider if developing a production client based on this file:
- checkpointing should be used:
  - Azure python library supports this out of the box for checkpoints stored in Azure.
    This client has an example for this, see variables STORAGE_ACCOUNT_NAME, STORAGE_KEY
    and LEASE_CONTAINER_NAME.
  - Checkpointing can be implemented without Azure, see DummyStorageCheckpointLeaseManager.
  - Make sure to keep track of checkpoint on a per partition basis.
- optionally proxy configuration should be specified if available
- partitions should be considered.
  - The azure python library (used here) automatically reads from all partitions.
  - If developing a custom solution, care may be needed to read from all partitions.
- add code to handle timeouts and reconnect upon failures.
  - See the used azure module for potential exceptions.
  - Double check per partition checkpointing for per partition reconnects.
"""

import logging
import os
import sys
import zlib

from sqlalchemy import create_engine
from amqp_consumer import AMQPConsumer

# --- Azure Event Hub credentials to access Flightradar24 Live Event feed -------------------------
# -------------------------------------------------------------------------------------------------
# --- Credentials below will be provided by Flightradar24 -----------------------------------------
CONNECTION_STRING = os.environ.get('EVENT_HUB_CONNECTION_STRING', 'Endpoint=sb://fr24-position-feed-2-westeurope.servicebus.windows.net/;SharedAccessKeyName=ilt-gv-ams-consumer;SharedAccessKey=AEk4rTlpnmJVMUH4WmUGc3y5Bd3Szg1+A+AEhFeqhJs=;EntityPath=ilt-gv-ams')
CONSUMER_GROUP = os.environ.get('EVENT_HUB_CONSUMER_GROUP', '$Default')
# -------------------------------------------------------------------------------------------------
# --- Optional, if set can be used to store queue offset in Azure cloud storage -------------------
STORAGE_CONNECTION_STR = os.environ.get('STORAGE_CONNECTION_STR', '')
BLOB_CONTAINER_NAME = os.environ.get('BLOB_CONTAINER_NAME', '')
# -------------------------------------------------------------------------------------------------
# --- Optional, if you're behind corporate firewall or proxy --------------------------------------
PROXY_HOSTNAME = os.environ.get('PROXY_HOSTNAME', '')
PROXY_PORT = os.environ.get('PROXY_PORT', '')
PROXY_USER = os.environ.get('PROXY_USER', '')
PROXY_PASS = os.environ.get('PROXY_PASS', '')
# --- Client name can be chosen by you to facilitate debugging if needed --------------------------
CLIENTNAME = os.environ.get('CLIENTNAME', 'python-example-consumer')

import psycopg2
import json
import geopandas as gpd
from shapely.geometry import Point
from shapely.geometry import shape
from shapely.wkt import loads

# Create database connection
conn = psycopg2.connect(host='localhost', port=5432, database='schiphol')
cursor = conn.cursor()

# load bounding box of The Netherlands
gdf = gpd.read_file('data/bbox_border_nl.geojson')
bbox = gdf['geometry'].iloc[0]

def on_receive_callback(gzip_data):
    content = read_content(gzip_data)
    print('Aircraft count', content['full_count'])
    del content['full_count']
    del content['version']

    if not content:
        raise RuntimeError('No flights included in response?')

    for flight_id in content.keys():
        inspect_flight(flight_id, content[flight_id])


def read_content(gzip_data):
    """
    Read compressed content, decompress and return parsed JSON
    """
    print(f"Received {len(gzip_data)} bytes")

    # expand compressed data and check byte lengths
    json_data = zlib.decompress(gzip_data)

    # parse JSON content
    content = json.loads(json_data)
    return content


def inspect_flight(flight_id, values):
    """
    Parse list of values for a flight
    """
    # flight_id == "0" -> heartbeat message, ignore
    if flight_id == "0":
        return
    # join the field names with provided values and list them
    
    column_names = ['addr', 'lat', 'lon', 'track', 'alt', 'speed',
             'squawk', 'radar_id', 'model', 'reg', 'last_update', 'origin',
             'destination', 'flight', 'on_ground', 'vert_speed', 'callsign', 'source_type', 'eta']
    
    # Create point geometry from coordinates
    flight_location = Point(values[2],values[1])

    # If point is within border of The Netherlands, parse and insert data to database
    if flight_location.intersects(bbox): 

        if len(values) > len(column_names):
            new_value = json.dumps(values[-1])
            values[-1] = new_value
            column_names.append('enhanced')

        data_dict = dict(zip(column_names, values))
        data_dict['flightid']=flight_id
        column_names.insert(0, 'flightid')
        values.insert(0, flight_id)
        

        insert_columns = ', '.join(column_names)
        insert_values = ', '.join([
        f"'{value}'" if isinstance(value, str) else (f"'{json.dumps(value)}'" if isinstance(value, dict) else str(value))
        for value in values
        ])

        # Create insert statement
        sql = 'insert into schiphol_traffic ({}) VALUES ({})'.format(insert_columns, insert_values)

        cursor.execute(sql)
        conn.commit()

def consume_amqp(callback=on_receive_callback):
    consumer = AMQPConsumer(connection_string=CONNECTION_STRING,
                            consumer_group=CONSUMER_GROUP,
                            storage_connection_string=STORAGE_CONNECTION_STR,
                            blob_container_name=BLOB_CONTAINER_NAME,
                            proxy_host=PROXY_HOSTNAME,
                            proxy_port=int(PROXY_PORT) if PROXY_PORT else None,
                            proxy_user=PROXY_USER, proxy_pass=PROXY_PASS)
    consumer.set_callback(callback)
    consumer.consume()


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)sZ %(message)s')
    print(__doc__)
    consume_amqp()
