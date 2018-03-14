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
from uuid import getnode

PORT1 = 8001
PORT2 = 8002
PORT3 = 8003
MAC = getnode()

# get own ip

import commands
ips = commands.getoutput("/sbin/ifconfig | grep -i \"inet\" | awk '{print $2}'")
HOST =  ips.split('\n')[0][5:]

from uuid import getnode as get_mac
macs2=get_mac()
print macs2   # converts mac to 48 bit integer


s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
s3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s3.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)

# protocol, ID of think root, cost to reach root, ID of sender


print('Socket created')

try:
	s1.bind((HOST, PORT1))
	s2.bind((HOST, PORT2))
	s3.bind((HOST, PORT3))
except socket.error as msg:
	print('Bind failed. Error Code : ' + msg.args[0] + ' Message ' + msg.args[1])
	sys.exit()

print('Socket bind complete')

s1.listen(10)
s2.listen(10)
s3.listen(10)
print('Socket now listening')

# SOURCE ID, DEST ID, PORT USED ON DEST
ROUTES = {
	(1,2): 3,
	(1,3): 1,
	(1,4): 2,
	(2,1): 3,
	(2,3): 2, 
	(2,4): 1,
	(3,1): 1,
	(3,2): 2,
	(3,4): 3,
	(4,1): 2,
	(4,2): 1,
	(4,3): 3,
}

#RP, DP, BP
#PORT, MAC, STATUS
PORTS = []
for i in range(1,4):
	PORTS.append([i, 0, 'DP'])

print(PORTS)

root = MAC
#print("root is " + str(root))
isRoot = True
dist = 0

def lookup_route(dest):
	return ROUTES[(int(HOST.split('.')[3]),int(dest.split('.')[3]))]

def BPDU_check(root, isRoot, dist, senderIP, senderID, newDist, newRoot):
	#checks BPDU message for improvement, updates if so and returns true
	#root with smaller ID
	#root with equal ID, shorter distance
	#equal both, but sender has smaller ID

	print "root is " + str(root)
	print "am i root " + str(isRoot)
	print "dist is " + str(dist)
	print "senderIP " + str(senderIP)
	print "senderID " + str(senderID)
	print "newDist " + str(newDist)
	print "newRoot " + str(newRoot)
	
	if newRoot < root or (newRoot == root and (newDist + 1) < dist) or (newRoot == root and (newDist + 1) == dist and senderID < MAC):
		isRoot = False
		root = newRoot
		dist = newDist + 1
		# todo: set all ports except one with ID to 
		for list in PORTS: 
			destport = lookup_route(senderIP)
			if list[0] == destport:
				list[2] = 'RP'
			else:
				list[2] = 'BP'
		return True
	else:
		return False

# BPDU FORMAT
# OPCODE(1), SENDERMAC, DISTROOT, ROOTID

def clientthread(conn, clientip, clientport): 
	# todo: add to ports
	iter = 0
	global root, isRoot, dist
	print root

	while 1:
		data = conn.recv(4096).rstrip().split(" ")
		if data == ['']:
			print "closing"
			conn.close()
			break
		if iter == 0:
			# find
			for list in PORTS:
				destport = lookup_route(clientip)
				if list[0] == destport:
					list[1] = data[1]
					break
		
		if data[0] == '1': #BPDU
			print "BPDU RECEIVED"
			if BPDU_check(root, isRoot, dist, clientip, long(data[1]), long(data[2]), long(data[3])): #smaller found
				isRoot = False
				root = long(data[3])
				dist = long(data[2]) + 1
				
				print str(isRoot)
				print str(root)
				print str(dist)
				
				for list in PORTS:
					destport = lookup_route(clientip)
					if list[0] == destport:
						list[2] = 'RP'
					else:
						list[2] = 'BP'				

				#forward to all other ports
				for i in range(1,5):
					if i == int(HOST.split('.')[3]):
						continue
					else:
						try:
							destport = lookup_route(clientip)
							senderSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
							senderSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
							senderSock.connect(('10.0.0.' + str(i), 8000 + destport))
							testmsg = "1 " + str(MAC) + " " + str(dist) + " " + str(root)
							print repr(testmsg)
							senderSock.send("1 " + str(MAC) + " " + str(dist) + " " + str(root))
							sleep(3)
							senderSock.close()
						except:
							print("failed on " + str(i))
							continue
					print PORTS
		elif data[0].rstrip() == "printports":
			print PORTS
			print "printing"
		elif data[0].rstrip() == "!q":
			break
		#else:
			#print data[0]
			#print type(data[0])
		iter = iter+1
		print iter
	sleep(1)
	conn.close()

def listenthread(s):
	#todo: init ports
#	for i in range(1,3):
#		PORTS.append((i, 0, 'DP'))

	while 1:
		conn, addr = s.accept()
		print('Connected with ' + str(addr[0]) + ':' + str(addr[1]))
		start_new_thread(clientthread, (conn, addr[0], addr[1]))
	s.close()

def sendthread():
	global MAC, dist, root, isRoot
	print "lol"
	print str(isRoot)
	while isRoot:
		for i in range(1,5):
			print str(i)
			if i == int(HOST.split('.')[3]):
				continue
			else:
				try:
					destport = lookup_route('10.0.0.' + str(i))
					print str(destport)
					senderSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					senderSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
					senderSock.connect(('10.0.0.' + str(i), 8000 + destport))
					msg = "1 " + str(MAC) + " " + str(dist) + " " + str(root)
					senderSock.send(msg)
					sleep(3)
					senderSock.close()
				except:
					print("failed on " + str(i))
			sleep(20)


start_new_thread(listenthread, (s1,))
start_new_thread(listenthread, (s2,))
start_new_thread(listenthread, (s3,))

sleep(5) #give other servers time to initialize
start_new_thread(sendthread, ())

while 1:
	sleep(1)
