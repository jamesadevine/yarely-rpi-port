import socket
import time

HOST = '127.0.0.1'
PORT = 9786

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.send('<content-item type="remote" content-type="text/html"><requires-file><sources><uri>http://www.bbc.co.uk/iplayer</uri></sources></requires-file></content-item>'.encode())
s.close()

