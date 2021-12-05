#!/usr/bin/env python3
"""
GS-Plug-n-Play Responder - a ua-profile subscribe/notify server

Author: Bruce Walker <bruce.walker@gmail.com>
created: November, 2021

Copyright (c) 2021, Bruce Walker -- see the file LICENSE.
"""

from const import SERVERPORT, SIP_MCAST_NET
import sockbits
import sipmsg
import eventloop

from selectors import EVENT_READ, EVENT_WRITE
import sys
import time
import sched
import queue

# XXX naughty global vars
q = queue.SimpleQueue()
srvsock = None

# options
loglvl = 0
# XXX this format is mandatory! Must be a path ending in a slash (folder):
#     'http://192.168.2.4/tftp/xyzzy/'
cfg_url = None

# XXX
logf = sys.stderr

def log(s, prio=0):
	if prio <= loglvl:
		print(f'{time.asctime()} | {s}', file=logf, flush=True)

def timestamp():
	log('timestamp', 3)
	eventloop.scheduler.enter(60, 0, timestamp)

def q_outgoing(pkt, toaddr):
	"""
	queue an outgoing UDP dgram
	- use this in place of sock.sendto(pkt, to)
	  insert msg in queue and enable tx-ready events
	"""
	q.put_nowait((pkt, toaddr))
	eventloop.selector.modify(srvsock, EVENT_READ|EVENT_WRITE, in_out)

def outgoing(sock):
	"""
	event: TX ready; pull next UDP packet from queue and send it
	handle outgoing UDP dgrams, both multi- and uni-cast
	"""
	try:
		pkt, toaddr = q.get_nowait()
		sock.sendto(pkt.encode(), toaddr)
		log(f'sendto {toaddr}: {pkt.encode()}', 2)

	except queue.Empty:
		eventloop.selector.modify(sock, EVENT_READ, in_out)

def response(msg, frm):
	"""
	we note any acknowledgement of our NOTIFY, but take no action.
	"""
	log(f'got "{msg.hdr_fields[0].raw}" from {frm}', 2)

def subscribe(msg, frm):
	"""
	test that any received SUBSCRIBE is well-formed and what we're waiting for;
	if so, queue up a NOTIFY message with the configuration URL.
	"""
	try:
		event = msg.find_1st('event').value
	except (AttributeError, TypeError):
		event = ''
	if event != 'ua-profile':
		return

	"""
	we only handle ua-profile subscribe requests for Grandstream phones
	per their Plug and Play "specification"
	"""
	try:
		vendor = msg.find_1st('event').find('vendor')[1]
	except (AttributeError, TypeError):
		vendor = 'unknown vendor'
	if vendor != 'Grandstream':
		log(f'SUBSCRIBE {frm[0]} {vendor}', 1)
		return

	try:
		mfrom = msg.find_1st('from').value
		model = msg.find_1st('event').find('model')[1]
		fwvers = msg.find_1st('event').find('version')[1]
	except (AttributeError, TypeError):
		mfrom = model = fwvers = ''
	mac = sipmsg.get_mac(mfrom).lower()

	"""
	log beacon
	  date | SUBSCRIBE mac:xxx 192.168.a.b Grandstream GRP2612W fw 1.0.5.67
	"""
	log(f'SUBSCRIBE mac:{mac} {frm[0]} {vendor} {model} fw {fwvers}')

	if cfg_url:
		""" unicast our '200 OK' response
		    send the profile path URL in a NOTIFY """
		q_outgoing(msg.response(), frm)
		send_ua_profile(msg, frm)
		log(f'NOTIFY {frm[0]} {cfg_url}', 1)

def send_ua_profile(msg, frm):
	"""
	queue a NOTIFY ua-profile event request with our config path URL in it
	"""
	# get client's uri -- eg 'sip:192.168.1.2:5080'
	clienturi = msg.find_1st('Contact').value.strip('<>')

	# our-end's addr
	our_addr = sockbits.my_addr_for(frm[0])
	our_uri = f'sip:daemon@{our_addr}'	# XXX not critical

	# rfc3261 sect 8.1.1.7
	import random
	magic_rand = f'z9hG4bK{random.randint(0,10000000000)}'

	nfy = sipmsg.msg()
	nfy.add_hdr(f'NOTIFY {clienturi} SIP/2.0', False)
	nfy.add_hdr(
		f'Via: SIP/2.0/UDP {our_addr}:{frm[1]};branch={magic_rand};rport')
	nfy.add_hdr(f'From: <{our_uri}>')
	nfy.add_hdr(f'To: <{clienturi}>')
	nfy.add_hdr(msg.find_1st('Call-ID').raw)	# just copy rx'ed one
	nfy.add_hdr(f'CSeq: 1 NOTIFY')				# XXX number should ascend
	nfy.add_hdr('Max-Forwards: 70')
	nfy.add_hdr('Event: ua-profile')
	#nfy.add_hdr('User-Agent: GS-Plug-n-Play daemon')	# XXX may be insecure
	nfy.add_hdr('Content-Type: application/url')
	nfy.body = f'{cfg_url}\r\n'
	nfy.add_hdr(f'Content-Length: {len(nfy.body)}')

	q_outgoing(nfy.request(), frm)		# unicast our notify request

def incoming(sock):
	"""
	event: rx-ready; handle incoming UDP dgrams, both multi- and uni-cast
	- separate them into SUBSCRIBE, OKAY, etc.
	"""
	pkt, frm = sock.recvfrom(1024) # frm is a tuple, eg ("192.168.86.30", 5080)
	req = pkt.decode()        # treat datagram as UTF-8 str

	m = sipmsg.msg(req)
	method = m.parse()
	log(f'received {method} from {frm}: {pkt}', 2)

	if method == 'SUBSCRIBE':
		subscribe(m, frm)
	elif method == 'RESPONSE':
		response(m, frm)

def in_out(sock, mask):
	"""
	sock was registered for both reading and writing; direct the event ...
	"""
	if mask & EVENT_READ:
		incoming(sock)
	if mask & EVENT_WRITE:
		outgoing(sock)

def main(argv):
	import getopt

	global loglvl, cfg_url
	brief = '''\
gspnp_responder [-vh] [url]
  -h   -- help; this message
  -v   -- verbose; extra debug stuff
  url  -- send configuration URL, eg http://192.168.1.2/gs/
          if no url, passively log beacons'''

	try:
		opts, args = getopt.getopt(argv[1:], "hv")
	except getopt.GetoptError:
		print(brief, file=sys.stderr)
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print(brief)
			sys.exit()
		elif opt == '-v':
			loglvl += 1		# pump up the volume

	if len(args) == 1:
		cfg_url = args[0]
	elif len(args) > 1:
		print(brief, file=sys.stderr)
		sys.exit(2)

	# open UDP socket
	# XXX naughty global var
	global srvsock
	srvsock = sockbits.open_socket(SERVERPORT, SIP_MCAST_NET)
	srvsock.setblocking(False)

	# register UDP socket for r/w with the event loop
	# EVENT_READ|EVENT_WRITE
	eventloop.selector.register(srvsock, EVENT_READ|EVENT_WRITE, in_out)

	if loglvl > 2:
		timestamp()		# run a heartbeat
	eventloop.run()		# never exits

if __name__ == "__main__":
	try:
		main(sys.argv)
	except KeyboardInterrupt:
		...

