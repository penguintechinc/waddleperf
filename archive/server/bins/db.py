#!/usr/bin/python3

from pydal import DAL, Field, IS_IPADDRESS, IS_ALPHANUMERIC, IS_LENGTH, IS_IN_SET
from dataclasses import dataclass
from re import search
import requests


@dataclass
class dbInfo: 
    dbName: str = 'waddleperf'
    dbUser: str = 'waddler'
    dbPass: str = ''
    dbHost: str = 'localhost'
    dbPort: str = '5432'
    dbType: str = 'mysql'
    

@dataclass
class perfInfo:
    testName: str
    testType: str
    testServerIP: str
    testClientIP: str
    testHost: str
    avgLatency: float
    avgThroughput: float
    avgJitter: float
    avgPacketLoss: float
    rawResults: str

class dbConnect:
    def __init__(self, dbInfo):
        self.db = DAL(dbInfo.DbType+'://'+dbInfo.dbUser+':'+dbInfo.dbPass+'@'+dbInfo.dbHost+':'+dbInfo.dbPort+'/'+dbInfo.dbName)
        self.db.define_table('testResults', 
                             Field('testName', 'string', required=True, requires = IS_ALPHANUMERIC()),
                             Field('testType', 'string', required=True, requires = IS_IN_SET(['sshping', 'iperf', 'httptrace', 
                                                                                              'pping-dns', 'pping-quic', 'pping-tcp', 
                                                                                              'pping-tls', 'pping-http','pping',
                                                                                              'traceroute','mtr', 'ping'])), 
                             Field('testHost', 'string', required=True, requires = IS_ALPHANUMERIC(), label='hostname which the test was for'), 
                             Field('testServerIP', 'string', requires = IS_IPADDRESS(), label='Acting Server host for testing'), 
                             Field('testClientIP', 'string', requires = IS_IPADDRESS(), label='Client host for testing'), 
                             Field('avgLatency', 'float'), 
                             Field('avgThroughput', 'float'), 
                             Field('avgJitter', 'float'), 
                             Field('avgPacketLoss', 'float'),
                             Field('rawResults', 'json', label='Raw results from test'))
    
    def insertPerfData(self, perfInfo):
        self.db.testResults.insert(testName=perfInfo.testName, 
                                   testType=perfInfo.testType, 
                                   testServerIP=perfInfo.testServerIP, 
                                   testClientIP=perfInfo.testClientIP, 
                                   avgLatency=perfInfo.avgLatency, 
                                   avgThroughput=perfInfo.avgThroughput, 
                                   avgJitter=perfInfo.avgJitter, 
                                   avgPacketLoss=perfInfo.avgPacketLoss,
                                   rawResults=perfInfo.rawResults)
    
    def queryTestName(self, testName):
        return self.db(self.db.testResults.testName == testName).select()
    
    def queryHostName(self, hostName):
        return self.db((self.db.testResults.testServerIP == hostName) | (self.db.testResults.testClientIP == hostName)).select()
    
    def close(self):
        self.db.close()
        
class logParser():
    def __init__(self, logFile):
        self.result = perfInfo
        self.logFile = logFile
        
    def iperf(self):
        import json
        try:
            with open(self.logFile, 'r') as file:
                perfData= json.load(file)
                file.close
            # TODO: CHange test name to be something onboarded as like a description later
            self.result.testName = "iperf"
            self.result.testType = "iperf"
            # TODO: Change this to be more dynamic later from request
            self.result.testHost = "nohost.local"
            self.result.rawResults = perfData
            self.result.testServerIP = getpublicIP()['icanhazip']
            self.result.testClientIP = perfData['start']['connected'][0]['remote_host']
            # Check if udp or tcp
            if perfData['start']['test_start']['protocol'] == 'UDP':
                # get packet loss
                self.result.avgPacketLoss = perfData['end']['sum']['lost_packets']
                # get mean latency
                self.result.avgLatency = perfData['end']['sum']['seconds']/ perfData['end']['sum']['packets']
                # get throughput
                self.result.avgThroughput = perfData['end']['sum']['bits_per_second']
                # get jitter
                self.result.avgJitter = perfData['end']['sum']['jitter_ms']
            elif perfData['start']['test_start']['protocol'] == 'TCP':
                # Get packet loss
                self.result.avgPacketLoss = perfData['end']['sum_sent']['retransmits'] 
                # Get mean latency
                self.result.avgLatency = perfData['end']['streams'][0]['sender']['mean_rtt']/2
                # Get throughput
                self.result.avgThroughput = perfData['end']['sum_received']['bits_per_second']
                if self.results.avgThroughput == 0:
                    self.result.avgThroughput = perfData['end']['sum_sent']['bits_per_second']
                # Get Jitter
                self.result.avgJitter = None
            return self.result
        except:
            print("Error parsing log file")
    def pping(self):
        with open(self.logFile, 'r') as file:
            perfData= file.readlines
            file.close
        self.result.testName = "pping"
        # We have to check the file name to see what type of test as the output is the same for each
        if 'http' in self.logFile:
            self.result.testType = "pping-http"
        elif 'dns' in self.logFile:
            self.result.testType = "pping-dns"
        elif 'quic' in self.logFile:
            self.result.testType = "pping-quic"
        elif 'tcp' in self.logFile:
            self.result.testType = "pping-tcp"
        elif 'tls' in self.logFile:
            self.result.testType = "pping-tls"
        else:
            self.result.testType = "pping"
        for line in perfData:
            if "avg" in line:
                line = line.strip(' ')
                latency = (line.split(',')[6]).split('=')[1]
                # This should capture the latency in ms from the output at bottom
                self.result.avgLatency = search(r'^(\d){1:5}', latency)
            if "packet loss" in line:
                self.result.avgPacketLoss = line.split(' ')[5]

class getpublicIP():
    def __init__(self):
        self.ip = {}
        # Migrate this to our own servers at some point
        self.ip["ipify"] = requests.get('https://api.ipify.org').text
        self.ip["icanhazip"] = requests.get('http://icanhazip.com').text
        return self.ip
        