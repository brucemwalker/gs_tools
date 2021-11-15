#!/usr/bin/env python3

"""
convert vCard contacts file(s) to Grandstream Addressbook XML

- Export vCard file from macOS Contacts
- or export from Google Contacts using vCard format (I recommend CSV instead)

Author: Bruce Walker <bruce.walker@gmail.com>
modified: Nov 14, 2021
created: Nov 9, 2021

Features
- to pretty-print the output: xmllint --format contacts.xml
- Starred contacts are listed when dialing
  and appear in a Starred tab of the Groups menu.

Notes:

Not a complete vCard parsing implementation.  I am handling just
enough to be able to import vCard content into Grandstream phonebooks.
Also I'm only testing with Apple macOS and Google Contacts generated
vCards so there may be missing stuff.

To-Do
=====
- -G group option to import all vCards into the named phonebook group
x test with Google Contacts exported vCard.
  - "categories" is aka tags
    https://datatracker.ietf.org/doc/html/rfc6350#section-6.7.1

References
==========
vCard v4.0 Format Specification
  https://datatracker.ietf.org/doc/html/rfc6350
Parameter Value Encoding in iCalendar and vCard
  https://datatracker.ietf.org/doc/html/rfc6868
vCard v3.0 Format Specification
  https://datatracker.ietf.org/doc/html/rfc2426
"""

BRIEF = 'usage: vcard2gs [-hfP] [-F faves] [-g inc-group [...]] [-o xml-file] [vcard-file [...]]'

HELP = f'''{BRIEF}

Convert a vCard file or stream into Grandstream phonebook XML records.

  -g group
          create an addressbook group 'group' and include contacts
          with this label in the named group.
          Every -g option adds another group.
  -f      include 'starred' contacts (faves) in a group
          called 'Starred' by default.
  -F name
          replace the default faves group name.
  -o file
          write Grandstream phonebook XML to 'file'.
          Output is written to standard output if this
          option is missing.
  -h      help (this text).
  -P      pretty-print phone numbers (warning: Grandstream phones
          misbehave with these).

Additional arguments are read in order for vCard records to include.
Standard input is read in the absence of args.

If no -g options or a -f option are specified all contacts found
in the given CSV files are included in the phonebook output.

If a -f or one or more -g options are given then only contacts
which are members of that group list are included in the phonebook
output.
'''

DEFAULT_FAVES = 'Starred'
GSTARRED = '* starred'

"""
Grandstream GRP26xx screws up dialing and phonebook editing
with any formating chars at all in the phone numbers.
    "Number is required and must only contain DTMF digits"
Set ENABLE_PRETTYPRINT=True to allow some formatting anyway.
-P   - enable pretty-print
"""
ENABLE_PRETTYPRINT = False

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

# add a new text sub-element to an element <el><sub>text value</sub></el>

def el_addtext(element, name, text):
	new_element = ET.SubElement(element, name)
	new_element.text = text
	return new_element

# reformat a phone number ph removing crap that confuses the phone
# - see notes above re Grandstream terminals.

def canon_number(ph):
	import re

	# 1st strip trailing extension then non-digits from phone number
	# - assume extension syntax: "x123", "ext 123"
	# - include * # in number digits; allows for *97 and #6
	num = re.sub('[xX].*$|[^0-9#*]', '', ph)

	if not ENABLE_PRETTYPRINT:
		return num		# return only digits to avoid confusing the GS phone

	# pretty-print NANP numbers -- note: this messes with Grandstream handset
	# - it can dial okay, but local contact editing is boogered.

	# don't try to fixup non-NANP numbers

	ld = False
	if len(num) == 11 and num[0] == '1':
		ld = True
		num = num[1:]
	if len(num) != 10:
		return num		# non-NANP; just use digits

	# get NANP number components

	pre, npa, nxx, ext = '1-' if ld else '', num[0:3], num[3:6], num[6:]
	return f'{pre}{npa}-{nxx}-{ext}'

# return the id for a phonebook group 'grp'
# - create a new one if not found

def get_or_insert_group(addrbook, grp):
	pbgroup = addrbook.find(f'./pbgroup[name="{grp}"]')
	if pbgroup:
		return pbgroup.find('id').text

	# new to us; add a new pbgroup

	pbgroup = ET.Element('pbgroup')
	el_addtext(pbgroup, 'name', grp)

	# set the new pbgroup id to the next higher

	gl = [int(el.find('id').text) for el in addrbook.findall('./pbgroup')]
	grp_id= str(max(gl)+1) if gl else "1"
	el_addtext(pbgroup, 'id', grp_id)
	addrbook.append(pbgroup)

	return grp_id

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

#BRIEF = 'usage: vcard2gs [-hfP] [-F faves] [-g inc-group [...]] [-o xml-file] [vcard-file [...]]'
#HELP = BRIEF # XXX for now ...

def main(argv):
	import os.path, sys, getopt

	out = sys.stdout
	incgroups = []
	faves = DEFAULT_FAVES

	try:
		opts, args = getopt.getopt(argv, "hfPF:g:o:")
	except getopt.GetoptError:
		print(BRIEF, file=sys.stderr)
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print(HELP)
			sys.exit()
		elif opt == '-P':
			global ENABLE_PRETTYPRINT
			ENABLE_PRETTYPRINT = True	# "Bad developer! No biscuit!"
		elif opt == '-o':
			out = arg
		elif opt == '-f':
			incgroups += [GSTARRED]
		elif opt == '-g':
			incgroups += [arg]
		elif opt == '-F':
			faves = arg

	addrbook = ET.Element('AddressBook')
	el_addtext(addrbook, 'version', '1')
	get_or_insert_group(addrbook, faves)

	if not args:
		vcard_to_phonebook(sys.stdin, addrbook, incgroups, faves)
	else:
		for vcardfile in args:
			if not os.path.isfile(vcardfile):
				print(f'{vcardfile}: not found', file=sys.stderr)
				continue
			with open(vcardfile, newline='') as cf:
				vcard_to_phonebook(cf, addrbook, incgroups, faves)

	# create the Grandstream-formatted XML phonebook

	with sys.stdout if out==sys.stdout else open(out, 'w') as f:
		f.write('<?xml version="1.0" encoding="UTF-8"?>')
		f.write(ET.tostring(addrbook, encoding="unicode"))

if __name__ == "__main__":
	import sys
	main(sys.argv[1:])

