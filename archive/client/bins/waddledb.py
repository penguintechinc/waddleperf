import argparse
import getopt
import logging
import re
import sys
from pydal import DAL, Field, IS_DATETIME, IS_FLOAT_IN_RANGE, IS_NOT_EMPTY
from dataclasses import dataclass
from datetime import datetime

def setup_logging(log_file=None):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def validate_db_host(host):
    ip_pattern = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    fqdn_pattern = re.compile(r"^(?=.{1,253}$)(?!-)[a-zA-Z0-9-]{1,63}(?<!-)(\.[a-zA-Z]{2,})+$")
    if ip_pattern.match(host) or fqdn_pattern.match(host):
        return True
    else:
        return False

def validate_db_port(port):
    if port.isdigit() and 0 < int(port) <= 65535:
        return True
    else:
        return False

def get_db_path():
    db_type = 'sqlite'
    db_host = 'localhost'
    db_port = '5432'
    log_file = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "thp", ["db_type=", "db_host=", "db_port=", "log_file="])
    except getopt.GetoptError as err:
        logger.error(str(err))
        sys.exit(2)
    for opt, arg in opts:
        if opt == "--db_type":
            if arg not in ['sqlite', 'mysql', 'postgres']:
                logger.error("Unsupported database type")
                sys.exit(2)
            db_type = arg
        elif opt == "--db_host":
            if validate_db_host(arg):
                db_host = arg
            else:
                logger.error("Invalid db_host. It should be a valid IP address or FQDN.")
                sys.exit(2)
        elif opt == "--db_port":
            if validate_db_port(arg):
                db_port = arg
            else:
                logger.error("Invalid db_port. It should be a number between 1 and 65535.")
                sys.exit(2)
        elif opt == "--log_file":
            log_file = arg

    logger = setup_logging(log_file)

    if db_type == 'sqlite':
        return 'sqlite://storage.sqlite'
    elif db_type == 'mysql':
        return 'mysql://username:password@localhost/dbname'
    elif db_type == 'postgres':
        return 'postgres://username:password@localhost/dbname'
    else:
        logger.error("Unsupported database type")
        sys.exit(2)

db_path = get_db_path()

class NetworkPerformanceDB:
    def __init__(self, db_path='sqlite://storage.sqlite'):
        self.db = DAL(db_path)
        self.define_tables()
        self.db.commit()

    def define_tables(self):
        self.db.define_table('network_performance',
                             Field('timestamp', 'datetime', requires=[IS_NOT_EMPTY(), IS_DATETIME()]),
                             Field('latency', 'double', requires=[IS_NOT_EMPTY(), IS_FLOAT_IN_RANGE(0, 5000)]),
                             Field('throughput', 'double', requires=[IS_NOT_EMPTY(), IS_FLOAT_IN_RANGE(0, 300000)]),
                             Field('packet_loss', 'double', requires=[IS_NOT_EMPTY(), IS_FLOAT_IN_RANGE(0, 100)]),
                             Field('destination_host', 'string', requires=[IS_NOT_EMPTY()]),
                             Field('user', 'string', requires=[IS_NOT_EMPTY()]),
                             Field('port', 'integer', requires=[IS_NOT_EMPTY(), IS_FLOAT_IN_RANGE(1, 65535)]))

    def insert_performance_data(self, data):
        if type(data) != NetworkPerformanceData:
            raise TypeError("data must be of type NetworkPerformanceData")
        self.db.network_performance.insert(timestamp=data.timestamp,
                            latency=data.latency,
                            throughput=data.throughput,
                            packet_loss=data.packet_loss, 
                            destination_host=data.destination_host, 
                            user=data.user, port=data.port)
        self.db.commit()

        @dataclass
        class NetworkPerformanceData:
            timestamp: datetime
            latency: float
            throughput: float
            packet_loss: float
            destination_host: str
            user: str
            port: int

    def close(self):
        self.db.close()