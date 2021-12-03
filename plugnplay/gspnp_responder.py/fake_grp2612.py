#!/usr/bin/env python3
"""
send a canned SUBSCRIBE for ua-profile event to the SIP multicast group
(request copied from an actual GRP2612W)

Author: Bruce Walker <bruce.walker@gmail.com>
created: November, 2021

Copyright (c) 2021, Bruce Walker -- see the file LICENSE.
"""

from const import MYADDRESS, SIPPORT, SIP_MCAST_NET
import sockbits
import sipmsg
import sys

def req():
	sock = sockbits.open_socket(MYADDRESS)		# open UDP socket

	#to = ('192.168.1.10', SIPPORT)		# XXX unicast a packet
	to = (SIP_MCAST_NET, SIPPORT)		# multicast a packet

	pkt = TEST_SUB_PKT
	sock.sendto(pkt, to)

try:
	req()
except KeyboardInterrupt:
	...

# XXX
TEST_SUB_PKT = b'''\
SUBSCRIBE sip:MAC%3AC074AD112233@224.0.1.75 SIP/2.0\r
Via: SIP/2.0/UDP 192.168.1.2:5080;branch=z9hG4bK1611133778;rport\r
From: <sip:MAC%3AC074AD112233@224.0.1.75>;tag=395400190\r
To: <sip:MAC%3AC074AD112233@224.0.1.75>\r
Call-ID: 490431573-5080-1@BJC.BGI.IG.DA\r
CSeq: 20000 SUBSCRIBE\r
Contact: <sip:192.168.1.2:5080>\r
Max-Forwards: 70\r
User-Agent: Grandstream GRP2612W 1.0.5.67\r
Expires: 0\r
Supported: replaces, path\r
Event: ua-profile;profile-type="device";vendor="Grandstream";model="GRP2612W";version="1.0.5.67"\r
Accept: application/url\r
Allow: INVITE, ACK, OPTIONS, CANCEL, BYE, SUBSCRIBE, NOTIFY, INFO, REFER, UPDATE, MESSAGE\r
Content-Length: 0\r
\r
'''

