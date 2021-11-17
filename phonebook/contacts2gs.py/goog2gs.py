#!/usr/bin/env python3

"""
convert Google Contacts CSV file to Grandstream Addressbook XML

- export from Google Contacts; use Google CSV format from All contacts

Author: Bruce Walker <bruce.walker@gmail.com>
created: Oct 28, 2021

Copyright (c) 2021, Bruce Walker -- see the file LICENSE.

Features
- ringtones per-contact are supported through Google contacts.
  - using a Custom Field, set the value to one of:
     'default ringtone', 'system', 'silent', 'ring1.bin', ...
  - set the Label to 'Ringtone'
- to pretty-print the output: xmllint --format contacts.xml
- Starred contacts are listed when dialing
  and appear in a Starred tab of the Groups menu.

To-Do
x deal with Blocklist/Allowlist vs Blacklist/Whitelist -- do I even need them?
x allow *97 as a phonenumber
"""

BRIEF = 'usage: goog2gs [-hfP] [-F faves] [-g inc-group [...]] [-o xml-file] [csv-file [...]]'

HELP = f'''{BRIEF}

Convert a Google Contacts CSV export into Grandstream phonebook
XML records.

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

Additional arguments are read in order for Google Contact CSV
records to include. Standard input is read in the absence of args.

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

"""
todo:
- in pbgroup spec, what does <Primary> do?

Implementation notes:
- GS phonebook contacts _must_ have:
  - a last name
  - at least one phone number
  - numbers may contain formating, but no trailing extension, etc.
    - stick to hyphens; brackets & spaces are questionable

refs
 https://docs.python.org/3/library/xml.etree.elementtree.html
 https://www.grandstream.com/hubfs/Product_Documentation/GXP_XML_phonebook_guide.pdf
"""

import xml.etree.ElementTree as ET

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

def main(argv):
	import sys, getopt, os.path

	out = sys.stdout
	incgroups = []
	faves = DEFAULT_FAVES

	try:
		opts, args = getopt.getopt(argv[1:], "hfPF:g:o:")
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
	# XXX just omit these now
	#get_or_insert_group(addrbook, 'Blocklist')
	#get_or_insert_group(addrbook, 'Allowlist')
	get_or_insert_group(addrbook, faves)

	if not args:
		csv_to_phonebook(sys.stdin, addrbook, incgroups, faves)
	else:
		for csvfile in args:
			if not os.path.isfile(csvfile):
				print(f'{csvfile}: not found', file=sys.stderr)
				continue
			with open(csvfile, newline='') as cf:
				csv_to_phonebook(cf, addrbook, incgroups, faves)

	# create the Grandstream-formatted XML phonebook

	with sys.stdout if out==sys.stdout else open(out, 'w') as f:
		f.write('<?xml version="1.0" encoding="UTF-8"?>')
		f.write(ET.tostring(addrbook, encoding="unicode"))

if __name__ == "__main__":
	from sys import argv
	main(argv)

