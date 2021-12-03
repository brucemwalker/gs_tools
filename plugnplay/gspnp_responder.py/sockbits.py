"""
sockbits.py -- socket functions

Author: Bruce Walker <bruce.walker@gmail.com>
created: November, 2021

Copyright (c) 2021, Bruce Walker -- see the file LICENSE.
"""

def my_addr_for(remote='8.8.8.8'):
	"""
	get the address that remote would use to reach back to me.
	"""
	import socket
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		s.connect((remote, 80))
		mine = s.getsockname()[0]
	except socket.gaierror:
		mine = '127.0.0.1'	# XXX whatever
	finally:
		s.close()
	return mine

def open_socket(addr, mcast=None):	# addr: ('host', port)
	"""
	open a tx/rx socket on the interface corresponding to addr
	- (also) listen for multicast datagrams in the mcast group if set
	  - for a tx-only use, setting the mcast parm is unnecessary
	- all interfaces if host is null string
	"""
	import socket

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind(addr)
	if mcast:
		import struct
		group = socket.inet_aton(mcast)
		mreq = struct.pack('4sL', group, socket.INADDR_ANY)
		sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)	
	return sock

