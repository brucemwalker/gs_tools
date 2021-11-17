"""
vCard format reader
- support:
    - Google Contacts 
	- macOS Contact.app

Author: Bruce Walker <bruce.walker@gmail.com>
created: Nov 17, 2021

Copyright (c) 2021, Bruce Walker -- see the file LICENSE.
"""

"""
Notes:

Not a complete vCard parsing implementation.  I am handling just
enough to be able to import vCard content into Grandstream phonebooks.
Also I'm only testing with Apple macOS and Google Contacts generated
vCards so there may be missing stuff.

References
==========
vCard v4.0 Format Specification
  https://datatracker.ietf.org/doc/html/rfc6350
Parameter Value Encoding in iCalendar and vCard
  https://datatracker.ietf.org/doc/html/rfc6868
vCard v3.0 Format Specification
  https://datatracker.ietf.org/doc/html/rfc2426
"""

import re

class vCard:
	'''
	container object that holds the content of one vCard.
	'''
	def __init__(self):
		self._prop_set = set()		# track the properties we have set

	def set(self, prop, val=''):
		p = self.nrmlzprop(prop)
		# properties are kept in an ordered list
		if p not in self._prop_set:
			setattr(self, p, [val])
			self._prop_set |= set([p])
		else:
			cur = getattr(self, p)
			cur.append(val)
			setattr(self, p, cur)

	def get(self, prop, default=''):
		try:
			val = getattr(self, self.nrmlzprop(prop))
			# if expecting a string, return just the first of multiple
			if isinstance(default, str):
				return val[0]
			else:
				return val

		except AttributeError:
			return default

	@staticmethod
	def nrmlzprop(prop):
		# 'item1.X-FOO-WONKA' => 'x_foo_wonka'
		# - deals with "group constructs" by erasing (RFC 6350 pg 7, pp 3)
		return re.sub('^[^.]*\\.', '', prop).replace('-','_').lower()

	@staticmethod
	def split_col(col):
		# subdivide semicolon-sep'ed mindfully of \-escapes
		return re.split('(?<!\\\\);', col)

	@staticmethod
	def split_subcol(col):
		# subdivide comma-sep'ed mindfully of \-escape
		return re.split('(?<!\\\\),', col)

	@staticmethod
	def property_param(pparam):
		return pparam.split('=')

	@staticmethod
	def unescape(text):
		# unescape stuff like \, \; etc. No need for us to fix \n
		# Alt: return re.sub('\\\\', '', text)
		return text.replace('\\','')

class vCardReader(vCard):
	'''
	an iterator object that reads a stream and returns found vCards
	'''
	def __init__(self, fd=None):
		self.stream = fd
		self.pushback = ""

	def read_line(self):
		if not self.pushback:
			return self.stream.readline()
		ln, self.pushback = self.pushback, ""
		return ln

	def pushback_line(self, ln):
		# XXX stack only one deep; if pushback != "", we should raise an alarm
		self.pushback = ln
		return

	# read the next input line plus line continuations

	def readline_unfolded(self):
		unfolded = self.read_line()
		while unfolded:
			peek = self.read_line()
			if not peek or peek[0] != ' ':
				self.pushback_line(peek)
				return unfolded
			unfolded = unfolded.rstrip('\r\n') + peek
		return ""	# EOF

	# read the next unfolded key-value line and split it; return False if EOF

	def next_key_value(self):
		try:
			ln = self.readline_unfolded()
			k, v = ln.split(':', 1)
			self.k = k.strip().lower()
			self.v = v.rstrip('\r\n')
			return True
		except ValueError:
			self.k, self.v = "", ""
			return False

	@staticmethod
	def factory():
		return vCard()

	# fetch the next vCard

	def next(self): return self.__next__()	# alias

	def __iter__(self):		# some iterator object magic
		return self

	def __next__(self):
		'''
		collect lines from a BEGIN to an END; unpack them into properties
		'''
		vcard = self.factory()

		# trash lines until BEGIN:VCARD -- loose RFC interpretation
		# XXX not RFC-compliant, and interferes with a "sniff test"

		while self.next_key_value():
			if self.k == 'begin' and self.v.lower() == 'vcard':
				break

		# collect vCard properties until END:VCARD

		while self.next_key_value():
			if self.k == 'end' and self.v.lower() == 'vcard':
				return vcard
			plist = vcard.split_col(self.k)
			prop = vcard.nrmlzprop(plist[0])
			vcard.set(prop, self.v)
			vcard.set(f'{prop}_params', ';'.join(plist[1:]))

		raise StopIteration

