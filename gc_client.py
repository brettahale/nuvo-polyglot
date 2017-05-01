#!/usr/local/bin/python

import socket

class GlobalCache:

    def __init__(self, host, port, logger):
        self.sock = None
        self.host = host
        self.port = port
        self.logger = logger


    def setup_socket(self):
        if self.sock is None:
            self.sock = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.logger.info("Connecting to socket {0}:{1}".format(self.host, str(self.port)))
        self.sock.connect((self.host, self.port))

    def msg(self, msg):
        try:
            if self.sock is None:
                self.logger.info("Setting up socket {0}:{1}".format(self.host, str(self.port)))
                self.setup_socket()

            self.logger.info("Sending msg {2} {0}:{1}".format(self.host, str(self.port), msg))
            sent = self.sock.send(msg + "\r\n")
            res = self.sock.recv(48)
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
            self.sock = None
            self.logger.info("recieved ({0}): {1}".format(len(res), res))
            if res == "#?":
                return False
            else:
                return res

        except:
            self.logger.info("Error Sending Command to Global Cache {0}".format(msg))
            return False

