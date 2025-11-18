#!/usr/bin/env python3

import sys
import getopt
from pydal import DAL, Field, IS_IPV4, IS_INT_IN_RANGE, IS_FLOAT_IN_RANGE, IS_IN_SET, IS_ALPHANUMERIC   
import yaml
from dataclasses import dataclass
import os
import json

DIRECTORY = '../data'
@dataclass
class Performance:
    dstHost: str
    dstPort: int
    dstProtocol: str
    srcHost: str
    ttl: int
    latencyMin: float
    latencyMean: float
    latencyMax: float
    geoRegion: str = None

class PerfDB:
    def __init__(self, args, config_path=None):
        default_db_uri = 'sqlite://../data/perfdb.sqlite'
        
        if config_path:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            db_uri = config.get('db_uri', default_db_uri)
        else:
            db_uri = default_db_uri
        
        self.db = DAL(db_uri)
        
        self.define_tables()
        self.db.commit()

    def define_tables(self):
        self.db.define_table('performance',
                             Field('dstHost', 'string', requires=[ IS_IPV4()], required=True),
                             Field('dstPort', 'integer', requires=IS_INT_IN_RANGE(1, 65536), required=True),
                             Field('dstProtocol', 'string', requires=IS_IN_SET(['TCP', 'UDP']), required=True),
                             Field('srcHost', 'string', requires=[ IS_IPV4()], required=True),
                             Field('ttl', 'integer', requires=IS_INT_IN_RANGE(1, 256), required=True),
                             Field('latencyMin', 'double', requires=IS_FLOAT_IN_RANGE(0, None), required=True),
                             Field('latencyMean', 'double', requires=IS_FLOAT_IN_RANGE(0, None), required=True),
                             Field('latencyMax', 'double', requires=IS_FLOAT_IN_RANGE(0, None), required=True),
                             Field('geoRegion', 'string', requires=IS_ALPHANUMERIC()))

    def insert_performance(self, performance: Performance):
        self.db.performance.insert(
            dstHost=performance.dstHost,
            dstPort=performance.dstPort,
            dstProtocol=performance.dstProtocol,
            srcHost=performance.srcHost,
            ttl=performance.ttl,
            latencyMin=performance.latencyMin,
            latencyMean=performance.latencyMean,
            latencyMax=performance.latencyMax,
            geoRegion=performance.geoRegion
        )
        self.db.commit()

    def get_performance(self, perfQuery: Performance):
        query = None
        if perfQuery.dstHost:
            query = (self.db.performance.dstHost == perfQuery.dstHost)
        elif perfQuery.srcHost:
            query = (self.db.performance.srcHost == perfQuery.srcHost)
        elif perfQuery.dstPort:
            query = (self.db.performance.dstPort == perfQuery.dstPort)
        if query:
            return self.db(query).select().as_dict()
        return []
    def insert_from_directory(self, directory: str = DIRECTORY):
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                with open(os.path.join(directory, filename), 'r') as file:
                    data = json.load(file)
                    performance = Performance(
                        dstHost=data['dstHost'],
                        dstPort=data['dstPort'],
                        dstProtocol=data['dstProtocol'],
                        srcHost=data['srcHost'],
                        ttl=data['ttl'],
                        latencyMin=data['latencyMin'],
                        latencyMean=data['latencyMean'],
                        latencyMax=data['latencyMax'],
                        geoRegion=data.get('geoRegion')
                    )
                    pdb.insert_performance(performance)

    def run(self, argv):
        config_path = None
        action = None
        dstHost = None
        dstPort = None
        dstProtocol = None
        srcHost = None
        ttl = None
        latencyMin = None
        latencyMean = None
        latencyMax = None
        geoRegion = None

        try:
            opts, args = getopt.getopt(argv, "hc:a:d:p:P:s:t:l:m:x:g:", ["config=", "action=", "dstHost=", "dstPort=", "dstProtocol=", "srcHost=", "ttl=", "latencyMin=", "latencyMean=", "latencyMax=", "geoRegion="])
        except getopt.GetoptError:
            print('perfDB.py -c <config_path> -a <action> -d <dstHost> -p <dstPort> -P <dstProtocol> -s <srcHost> -t <ttl> -l <latencyMin> -m <latencyMean> -x <latencyMax> -g <geoRegion>')
            sys.exit(2)
        for opt, arg in opts:
            if opt == '-h':
                print('perfDB.py -c <config_path> -a <action> -d <dstHost> -p <dstPort> -P <dstProtocol> -s <srcHost> -t <ttl> -l <latencyMin> -m <latencyMean> -x <latencyMax> -g <geoRegion>')
                print('Available actions are insert and get')
                sys.exit()
            elif opt in ("-c", "--config"):
                config_path = arg
            elif opt in ("-a", "--action"):
                action = arg
            elif opt in ("-d", "--dstHost"):
                dstHost = arg
            elif opt in ("-p", "--dstPort"):
                dstPort = int(arg)
            elif opt in ("-P", "--dstProtocol"):
                dstProtocol = arg
            elif opt in ("-s", "--srcHost"):
                srcHost = arg
            elif opt in ("-t", "--ttl"):
                ttl = int(arg)
            elif opt in ("-l", "--latencyMin"):
                latencyMin = float(arg)
            elif opt in ("-m", "--latencyMean"):
                latencyMean = float(arg)
            elif opt in ("-x", "--latencyMax"):
                latencyMax = float(arg)
            elif opt in ("-g", "--geoRegion"):
                geoRegion = arg

        pdb = PerfDB(config_path)

        if action == 'insert':
            if None in [dstHost, dstPort, dstProtocol, srcHost, ttl, latencyMin, latencyMean, latencyMax]:
                print('Error: Missing required fields for insert action. Please provide at minimum dstHost, dstPort, dstProtocol, srcHost, ttl, latencyMin, latencyMean, and latencyMax.')
                sys.exit(2)
            performance = Performance(dstHost, dstPort, dstProtocol, srcHost, ttl, latencyMin, latencyMean, latencyMax, geoRegion)
            pdb.insert_performance(performance)
        elif action == 'get':
            perfQuery = Performance(dstHost, dstPort, dstProtocol, srcHost, ttl, latencyMin, latencyMean, latencyMax, geoRegion)
            records = pdb.get_performance(perfQuery)
            for record in records:
                print(record)

if __name__ == "__main__":
    m = PerfDB()
    m.run(sys.argv[1:])
  