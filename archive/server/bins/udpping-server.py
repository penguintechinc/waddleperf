#!/usr/bin/env python3

import os
import sys
import getopt
import subprocess
import logging

def main(argv):
    log_level = logging.INFO
    token = None
    try:
        opts, args = getopt.getopt(argv, "hp:a:l:t:", ["port=", "address=", "loglevel=", "token="])
    except getopt.GetoptError:
        print('Usage: udpping-server.py -p <port> -a <address> -l <loglevel> -t <token>')
        sys.exit(2)

    port = 2000
    address = '0.0.0.0'
    for opt, arg in opts:
        if opt == '-h':
            print('Usage: udpping-server.py -p <port> -a <address> -l <loglevel> -t <token>')
            print('Example: udpping-server.py -p 2000 -a 0.0.0.0 -l INFO -t mytoken')
            print("Default port is 2000 and default address is 0.0.0.0")
            sys.exit()
        elif opt in ("-p", "--port"):
            port = arg
        elif opt in ("-a", "--address"):
            address = arg
        elif opt in ("-l", "--loglevel"):
            log_level = getattr(logging, arg.upper(), logging.INFO)
        elif opt in ("-t", "--token"):
            token = arg

    logging.basicConfig(level=log_level)
    logger = logging.getLogger(__name__)
    
    import socket
    import base64
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((address, int(port)))

    logger.info(f"Listening on UDP port {port} at address {address}")

    while True:
        data, addr = sock.recvfrom(1024)
        message = data.decode('utf-8')
        if token:
            encoded_token = base64.b64encode(token.encode('utf-8')).decode('utf-8')
            if message.startswith(encoded_token):
                logger.info(f"Received authenticated message: {message} from {addr}")
                response = message[len(f"Token {token} "):].encode('utf-8')
                sock.sendto(response, addr)
            else:
                logger.warning(f"Received unauthenticated message: {message} from {addr}")
        else:
            logger.info(f"Received message: {message} from {addr}")
            sock.sendto(data, addr)

if __name__ == "__main__":
    main(sys.argv[1:])
