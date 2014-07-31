import socket
import time

HOST = '148.88.227.126'
PORT = 9786

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.send(b'<web_request url="http://news.bbc.co.uk"/>')
s.close()

time.sleep(10)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.send(b"<web_request url=\"http://www.ravelry.com\"/>")
s.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.send(b"<web_request url=\"http://www.google.com\"/>")
s.close()

time.sleep(10)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.send(b"<web_request url=\"http://news.bbc.co.uk\"/>")
s.close()
