#!/usr/bin/env python3
from flask import Flask, request, jsonify
from geoip2 import database as ipDB

app = Flask(__name__)



@app.route('/ip', methods=['GET'])
def ip():
    output = {"RequestClientIP": request.remote_addr, "X-Forwarded-For": request.headers.get('X-Forwarded-For'), "X-Real-IP": request.headers.get('X-Real-IP')}
    if 'X-Forwarded-For' in request.headers:
        output["IP"] = request.headers['X-Forwarded-For'].split(',')[0].strip()
        output["Method"] = 'X-Forwarded-For'
    elif 'X-Real-IP' in request.headers:
        output["IP"] = request.headers['X-Real-IP']
        output["Method"] = 'X-Real-IP'
    else:
        output["IP"] = request.environ['REMOTE_ADDR']
        output["Method"] = 'REMOTE_ADDR'
    # The server will use geolite2 to lookup the user's location based on the IP address
    #output["Location"] = 
    return jsonify(output)

def lookupDetails(ip: str) -> dict:
    # The server will use geolite2 to lookup the user's location based on the IP address
    results = {"city": "Unknown", "country": "Unknown"}
    try:
        
        reader = ipDB.Reader('/opt/geoip/GeoLite2-City.mmdb')
        results["city"] = reader.city(ip).city.name
        results["country"] = reader.country(ip).country.name
        
        return results
    except:
        return "Unknown"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

