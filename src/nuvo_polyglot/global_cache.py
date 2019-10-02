#!/usr/bin/env python3

import socket, select
import logging
from time import sleep

class GlobalCache:

    def __init__(self, host, port, timeout=None):
        self.sock = None
        self.host = host
        self.port = port
        self.timeout = timeout or 5

    def _setup_socket(self):
        if self.sock is None:
            self.sock = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # self.sock.settimeout(self.timeout)

    def _connect(self):
        if self.sock is None:
            print("Setting up socket {0}:{1}".format(self.host, str(self.port)))
            self._setup_socket()
        print("Connecting to socket {0}:{1}".format(self.host, str(self.port)))
        self.sock.connect((self.host, int(self.port)))

    def msg(self, msg):
        totalsent = 0
        msg = "{}\r\n".format(msg).encode()
        msglen = len(msg)
        try:
            self._connect()
            print("Sending msg {2} {0}:{1}".format(self.host, str(self.port), msg))
            while totalsent < msglen:
                sent = self.sock.send(msg[totalsent:])
                if sent == 0:
                    raise RuntimeError("socket connection broken")
                totalsent = totalsent + sent

            print("Sent msg {2} {0}:{1}".format(self.host, str(self.port), msg))
            r, _, _ = select.select([self.sock], [], [])
            if r:
                result=[]
                chunks = []
                bytes_recd = 0
                while bytes_recd < msglen:
                    chunk = self.sock.recv(64)
                    if chunk == b'':
                        raise RuntimeError("socket connection broken")
                    chunks.append(chunk)
                    bytes_recd = bytes_recd + len(chunk)
            else:
                return False

            res_str = b"".join(chunks)
            print("recieved ({0}): {1}".format(len(res_str.decode()), res_str.decode()))
            if res_str == "#?":
                return False
            else:
                return res_str.decode()

        except(ConnectionRefusedError):
            logging.error("Can not connect to GlobalCache device at {}:{}".format(self.host, self.port))
            raise ConnectionRefusedError
        except(socket.timeout):
            logging.error("Timeout connecting to GlobalCache device at {}:{}".format(self.host, self.port))
            raise socket.timeout
        finally:
            self.sock.close()
            self.sock = None
            sleep(0.05)
