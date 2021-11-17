"""
import contacts file to xml tree
- support:
    - Google Contacts CSV and vCard
	- macOS vCard

Author: Bruce Walker <bruce.walker@gmail.com>
created: Nov 17, 2021

Copyright (c) 2021, Bruce Walker -- see the file LICENSE.
"""

import xml.etree.ElementTree as ET
from pbxml import *
from util import *

# return the string value of a column from a CSV row
# - else return default value (default-default: empty string)

def getcol(row, column_name, default=""):
	cs = row.get(column_name)
	return cs.strip() if cs else default

# return the value list of a column from a CSV row
# - else return an empty list
# XXX should not return empty (null string) list items

def getsubcol(row, column_name):
	col = getcol(row, column_name)
	if not col:
		return []

	# Google Contacts sub-divides multi-value columns with ':::'

	return [s.strip() for s in col.split(':::')]

# slurp the content of CSV stream csvin into Grandstream phonebook
#
# skip CSV records that:
# - have no phone number(s)
# - have no name or company name
# - aren't in our list of groups (labels) to include

def csv_to_phonebook(csvin, phonebook, incgroups, faves):
	import csv

	reader = csv.DictReader(csvin)
	for row in reader:

		# include only Contacts in the listed groups,
		#   or all Contacts if no groups specified

		groups = getsubcol(row, 'Group Membership')
		if incgroups:
			gi = list(set(incgroups) & set(groups))
			if not gi:
				continue
			groups = gi

		lname = getcol(row, 'Family Name')
		fname = getcol(row, 'Given Name')
		company = getcol(row, 'Organization 1 - Name')

		# a Contact is only valid if it at least has a last name
		# hack: use the Company as a "lastname" if we can

		if not lname:
			if company:
				lname = company
			else:
				continue

		contact = ET.Element('Contact')
		el_addtext(contact, 'LastName', lname)
		el_addtext(contact, 'FirstName', fname)
		el_addtext(contact, 'Company', company)

		el_addtext(contact, 'Department',
			getcol(row, 'Organization 1 - Department'))
		el_addtext(contact, 'JobTitle',
			getcol(row, 'Organization 1 - Title'))

		# add one or more numbers from each multi-value phone column

		for i in range(1, 5):
			phones = getsubcol(row, f'Phone {i} - Value')
			ptype = getcol(row, f'Phone {i} - Type')
			if ptype == 'Mobile':	# a little GS weirdosity
				ptype = 'Cell'

			for ph in phones:
				cphone = ET.SubElement(contact, 'Phone', type=ptype)
				el_addtext(cphone, 'phonenumber', canon_number(ph))
				# ToDo: 'accountindex'; call out on which SIP acct
				#       0 is 'Auto' -- ???

		# contact is only valid if it has one or more phone numbers

		if not contact.find('Phone'):
			continue

		# look for and add ringtone values from Ringtone custom field
		# XXX I don't actually know how many custom fields there can be.

		for i in range(1, 11):
			if (getcol(row, f'Custom Field {i} - Type') == 'Ringtone'):
				el_addtext(contact, 'RingtoneUrl',
					getcol(row, f'Custom Field {i} - Value'))
				break

		# add group membership

		for grp in groups:
			if grp == GSTARRED:
				grp = faves		# populate a 'faves' group
								# and set the Frequent contact flag
				el_addtext(contact, 'Frequent', '1')
			elif grp[0] == '*':	# ignore '* myContacts'
				continue
			el_addtext(contact, 'Group', get_or_insert_group(phonebook, grp))

		# insert this fully-fleshed Contact to the phonebook

		phonebook.append(contact)

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

import xml.etree.ElementTree as ET

# slurp the content of vCard stream vcardin into Grandstream phonebook
#
# skip vCards that:
# - have no phone number(s)
# - have no name or company name
# - aren't in our list of groups (labels) to include

def vcard_to_phonebook(vcardin, phonebook, incgroups, faves):

	reader = vCardReader(vcardin)
	for vc in reader:

		# include only Contacts in the listed groups,
		#   or all Contacts if no groups specified

		groups = []
		for g in vc.get('categories', []):	# supported by Google
			groups += vc.split_subcol(g)
		if incgroups:
			gi = list(set(incgroups) & set(groups) - set(['myContacts']))
			if not gi:
				continue
			groups = gi

		lst = vc.split_col(vc.get('n', ';;;;'))
		lname = vc.unescape(lst[0])
		fname = vc.unescape(lst[1])
		fn = vc.unescape(vc.get('fn'))

		lst = vc.split_col(vc.get('org', ';'))
		company = vc.unescape(lst[0])
		department = vc.unescape(lst[1]) if len(lst) > 1 else ""

		# a Contact is only valid if it at least has a last name
		# hack: use the Company as a "lastname" if we can
		# Is this macOS extension useful?
		#	X-ABShowAs:COMPANY

		if not lname:
			if fn:
				lname, fname = fn, ""
			elif company:
				lname = company
			elif fname:
				lname, fname = fname, ""
			else:
				continue		# ignore this anonymous contact

		contact = ET.Element('Contact')
		el_addtext(contact, 'LastName', lname)
		el_addtext(contact, 'FirstName', fname)
		el_addtext(contact, 'Company', company)
		el_addtext(contact, 'Department', department)

		el_addtext(contact, 'JobTitle', vc.unescape(vc.get('title')))
		el_addtext(contact, 'Job', vc.unescape(vc.get('role')))

		# add numbers from all TEL properties

		phones = vc.get('tel', [])
		parms = vc.get('tel_params', [])

		for i in range(0, len(phones)):
			ph = vc.unescape(phones[i])
			pp = vc.split_col(parms[i])

			# determine type of phone; ignore FAX machines
			# XXX ToDo: handle type=pref

			ptype=''
			if 'type=fax' in pp:
				continue
			if 'type=work' in pp:
				ptype='Work'
			elif 'type=home' in pp:
				ptype='Home'
			elif 'type=cell' in pp:
				ptype='Cell'

			cphone = ET.SubElement(contact, 'Phone', type=ptype)
			el_addtext(cphone, 'phonenumber', canon_number(ph))

		# contact is only valid if it has one or more phone numbers

		if not contact.find('Phone'):
			continue

		# XXX custom fields aren't supported in vCard export from Google,
		#     so no GS ringtones.

		# add group membership -- applies to Google Contacts

		for grp in groups:
			if grp == GSTARRED:
				grp = faves		# populate a 'faves' group
								# and set the Frequent contact flag
				el_addtext(contact, 'Frequent', '1')
			elif not grp or grp[0] == '*':	# ignore '* myContacts'
				continue
			el_addtext(contact, 'Group', get_or_insert_group(phonebook, grp))

		# insert this fully-fleshed Contact to the phonebook

		phonebook.append(contact)

