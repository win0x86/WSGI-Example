#!/usr/bin/env python
# coding: utf-8
"""
 https://www.python.org/dev/peps/pep-3333/
 https://wiki.python.org/moin/WebProgramming

WSGIServer example.

"""

import sys
import time
import socket
import datetime
import cStringIO


def default_app(environ, start_response):
    status = "200 OK"
    response_headers = [("Content-Type", "text/plain")]
    start_response(status, response_headers)
    return ["Hello world"]


def myapp(environ, start_response):
    status = "200 OK"
    ret = [
        "<DOCTYPE html>"
        "<html>"
        "<body>"
        "<h1>Hello WSGIServer!</h1>"
        "</body>"
        "</html>"
    ]
    response_headers = [
        ("Content-Type", "text/html; charset=utf-8"),
        ("Content-Length", len(ret[0]))
    ]
    start_response(status, response_headers)
    return ret


class WSGIServer(object):
    def __init__(self, host=None, port=None, app=None):
        self.host = host or "127.0.0.1"
        self.port = port or 8888
        self.app = app or default_app
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.sock.bind((self.host, self.port))
        self.sock.listen(128)
        print "Listen on %s: %s" % (self.host, self.port)

    def start_response(self, status, response_headers):
        server_headers = [
            ("Server", "WSGI Server")
        ]
        self.headers = response_headers + server_headers
        self.status = status

    def get_env(self, remote_ip, body):
        lines = body.split("\r\n")
        first_line = lines[0]
        method, path, version = first_line.split(" ")
        query, protocol = "", "http"
        environ = {
            "REQUEST_METHOD": method,
            "SCRIPT_NAME": "",
            "PATH_INFO": path,
            "QUERY_STRING": query,
            "REMOTE_ADDR": remote_ip,
            "SERVER_NAME": self.host,
            "SERVER_PORT": self.port,
            "SERVER_PROTOCOL": version,
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": protocol,
            "wsgi.input": cStringIO.StringIO(body),
            "wsgi.errors": sys.stderr,
            "wsgi.multithread": False,
            "wsgi.multiprocess": True,
            "wsgi.run_once": False,
        }
        return environ

    def generate(self, env, data):
        ret = "%s %s\r\n" % (env["SERVER_PROTOCOL"], self.status)
        for header in self.headers:
            ret += "%s: %s\r\n" % header
        ret += "\r\n"
        for d in data:
            ret += d
        return ret

    def serve(self):
        while True:
            conn, addr = self.sock.accept()
            data = ""
            start_time = time.time()
            recv = conn.recv(1024)
            if not recv:
                break
            data += recv

            env = self.get_env(addr[0], data)
            env["response_time"] = time.time() - start_time
            response = self.app(env, self.start_response)
            output = self.generate(env, response)
            print "[%s] %.4f ms %s" % (
                datetime.datetime.now(),
                env["response_time"] * 1000,
                env["PATH_INFO"]
            )
            conn.sendall(output)
            conn.close()


if __name__ == "__main__":
    server = WSGIServer(app=myapp)
    server.serve()
