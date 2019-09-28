#!/usr/bin/env python3

import socket
import logging

class GlobalCache:

    def __init__(self, host, port, timeout=None):
        self.sock = None
        self.host = host
        self.port = port
        self.timeout = timeout or 30

    def _setup_socket(self):
        if self.sock is None:
            self.sock = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(self.timeout)
        print("Connecting to socket {0}:{1}".format(self.host, str(self.port)))
        self.sock.connect((self.host, int(self.port)))


    def msg(self, msg):
        try:
            if self.sock is None:
                print("Setting up socket {0}:{1}".format(self.host, str(self.port)))
                self._setup_socket()

            print("Sending msg {2} {0}:{1}".format(self.host, str(self.port), msg))
            sent = self.sock.send("{}\r\n".format(msg).encode())
            res = self.sock.recv(48)
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
            self.sock = None
            print("recieved ({0}): {1}".format(len(res), res))
            if res == "#?":
                return False
            else:
                return res

        except(ConnectionRefusedError):
            logging.error("Can not connect to GlobalCache device at {}:{}".format(self.host, self.port))
            raise ConnectionRefusedError
        except(socket.timeout):
            logging.error("Timeout connecting to GlobalCache device at {}:{}".format(self.host, self.port))
            raise socket.timeout
