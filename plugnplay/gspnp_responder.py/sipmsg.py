"""
sipmsg.py -- SIP message object

Author: Bruce Walker <bruce.walker@gmail.com>
created: November, 2021

Copyright (c) 2021, Bruce Walker -- see the file LICENSE.
"""

import re

MANDATORY = ['Via', 'From', 'To', 'Call-ID', 'CSeq', 'Max-Forwards']

def get_addr(s):
	"""
	parse a SIP address into useful parts
	XXX needs to be expanded (a lot) if more SIPiness is desired
		covers basic needs for the ua-profile stuff
	"""
	#               'lalala <sip:192.168.1.2:5080> xxx'
	addr = re.compile('^[^<]*<([^:]+):([^:]+):([^:]+)>')
	try:
		method, host, port = addr.match(s).groups()
	except AttributeError:
		method, host, port = "","",""
	return method, host, port

def get_mac(s):
	"""
	parse a special MAC-SIP address to extract just the MAC
	"""
	#               'lalala <sip:MAC%3AC074AD112233@224.0.1.75> xxx'
	addr = re.compile('^[^<]*<[^:]+:MAC%3A([0-9A-Fa-f]{12})[^>]*>')
	try:
		mac = addr.match(s).groups()[0]
	except AttributeError:
		mac = ''
	return mac

class hdr_field():
	"""
	raw = 'From: <sip:MAC%3AC074AD112233@224.0.1.75>;tag=395400190;rport'
	name = 'From'
	value = '<sip:MAC%3AC074AD112233@224.0.1.75>'
	parms = [('tag', '395400190'),('rport', None)]
	"""
	def __init__(self, raw):
		self.raw = raw

	def parse(self):
		"""
		split out raw into components
		"""
		nm, v = self.raw.split(':', 1)
		self.name = nm.strip()
		hdrbits = v.strip().split(';')
		self.value = hdrbits[0].strip()

		self.parms = []
		for parm in hdrbits[1:]:
			hsb = parm.split('=',1)
			pn = hsb[0]
			pv = hsb[1].strip('" \t') if len(hsb) > 1 else None
			self.parms += [(pn, pv)]

	def find(self, name, default=None):
		"""
		find the header-field-parameter tuple with name 'name'
		return the tuple
		"""
		try:
			return [hfp for (i, hfp) in enumerate(self.parms)
				if hfp[0].lower() == name.lower()][0]
		except IndexError:
			return default

class msg():
	"""
	hdr_fields = [hdr_field obj, ...]
	body = str
	pkt = str 'lalala\r\nlalala ...'
	"""

	def __init__(self, pkt=None):
		self.pkt = pkt

	def add_hdr(self, raw, parse=True):
		"""
		add a new raw header field to the list hdr_fields
		"""
		try:
			hf = hdr_field(raw)
			if parse:
				hf.parse()
			self.hdr_fields += [hf]
			""" except ValueError: ...  """
		except AttributeError:
			self.hdr_fields = [hf]

	def parse(self):
		"""
		deconstruct the pkt string into interesting parts;
		if anything blows up, assume it's crap and bail.
		"""
		try:
			hdr, self.body = self.pkt.split('\r\n\r\n', 1)
			hdrlist = hdr.split('\r\n')

			self.add_hdr(hdrlist[0], parse=False)
			[self.add_hdr(s) for s in hdrlist[1:]]

			method = hdrlist[0].split()[0].upper()
			if method.startswith('SIP/2.0'):
				method = 'RESPONSE'

		except (ValueError, AttributeError):
			method = 'CRAP'
		return method

	def find_1st(self, name, default=''):
		"""
		find a header-field object with name 'name'
		returns the first match string
		"""
		try:
			return self.find(name)[0]
		except IndexError:
			return default

	def find(self, name):
		"""
		find all header-field objects with name 'name'
		returns a (possibly empty) list
		"""
		return [hf for (i, hf) in enumerate(self.hdr_fields[1:])
			if hf.name.lower() == name.lower()]

	def response(self, num='200', txt='OK'):
		"""
		return a suitably formatted response string
		include all the mandatory original headers from the msg
		"""
		resp = [f'SIP/2.0 {num} {txt}']
		resp += [self.find_1st(h).raw for h in MANDATORY]
		resp += ['']
		return '\r\n'.join(resp) + '\r\n'

	def request(self):
		"""
		return a suitably formatted request packet string
		"""
		resp = [h.raw for h in self.hdr_fields]
		resp += ['']
		return '\r\n'.join(resp)  + '\r\n' + self.body

