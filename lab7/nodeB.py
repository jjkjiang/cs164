#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  forwarder.py
#  
#  Copyright 2018 Jerry Jiang <jjian014@wch129-29.cs.ucr.edu>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import socket
import sys
from thread import *
from time import sleep

NODE = 'B'
IP = '10.0.100.3'
HOST = ''
PORT = 8001
MAC = '08:00:27:58:32:0d'

NETWORK = [('',8000), ('',8002), ('',8003)]

#tuples of mac, ip, ttl, port
ARP_TABLE = []

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)

fwlist = [["Client IP", "Client Port", "Server IP", "Server Port", "Message"]]

print('Socket created')

try:
	s.bind((HOST, PORT))
except socket.error as msg:
	print('Bind failed. Error Code : ' + msg.args[0] + ' Message ' + msg.args[1])
	sys.exit()

print('Socket bind complete')

s.listen(10)
print('Socket now listening')

# OPCODE,DATA,DATA...
# OPCODE,SENDERMAC,SENDERIP,SENDERPORT,RECVMAC,RECVIP,RECVPORT

def clientthread(conn, clientip, clientport):
	data = conn.recv(4096).replace(" ",",").split(",")
	if data[0] != '1': #not arp
		if data[0] == 'pingmac' and data[0][2] != ':':
			if [entry for entry in ARP_TABLE if entry[0] == data[1]]:
				print "lol"
				print entry[0]
			else:
				#todo make arp request here
				for element in NETWORK:
					try:
						clientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                               			clientSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
                               			clientSock.connect(element)
						senddata = [1, MAC, IP, PORT, '00:00:00:00:00:00', data[1], element[1]]
						clientSock.send(",".join([str(a) for a in senddata]))
					except:
						print "failed on " + str(element)
						continue
					sleep(1)
					reply = clientSock.recv(4096).split(",")
					if reply[0].rstrip() == '0':
						continue

					print "ARP returned from " + reply[3]
					#print reply
					nextentry = (reply[1], reply[2], "60s", reply[3])
					ARP_TABLE.append(nextentry)
					clientSock.send("pingmac " + reply[1])
					sleep(1)
					response = clientSock.recv(1024)
					print response
		if data[0].rstrip() == 'arp':
			print ARP_TABLE
			conn.send(str(ARP_TABLE))
		else:
			print data[:]
	elif data[0] == '1': #arp req
		print data[5]
		print IP
		if data[5].rstrip() == IP.rstrip():
			print "Received ARP from " + data[2] + " replying..."
			ARP_TABLE.append((data[1], data[2], "60s", data[3]))
			#senddata = [2, data[3:6], MAC, *data[1:3]]
			senddata = [2, MAC, IP, PORT, data[1], data[2], data[3]]
			# OPCODE,SENDERMAC,SENDERIP,SENDERPORT,RECVMAC,RECVIP,RECVPORT
			#senddata.extend(data[3:6])
			#senddata[2] = MAC
			#senddata.extend(data[0:3])
			#print senddata
			conn.send(",".join([str(a) for a in senddata]))

			newdata = conn.recv(4096).split(" ")

			#print "newdata = " + str(newdata)
			if newdata[1].rstrip() == MAC:
				print "pingmac received"
				conn.send("pingmac received")
			else:
				conn.send("error")
		else:
			print "Received ARP from " + data[2] + " ignoring..."
			conn.send("0")


	sleep(1)
	conn.close()


while 1:
	conn, addr = s.accept()
	print('Connected with ' + str(addr[0]) + ':' + str(addr[1]))

	start_new_thread(clientthread, (conn, addr[0], addr[1]))

s.close()
