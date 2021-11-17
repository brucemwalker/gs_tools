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

# default name Google Contacts uses for favourites group
GSTARRED = '* starred'

# return the string value of a column from a CSV row
# - else return default value (default-default: empty string)

def getcol(row, column_name, default=""):
	cs = row.get(column_name)
	return cs.strip() if cs else default

# Google Contacts sub-divides multi-value columns with ':::'
# return the value list of a column from a CSV row
# - else return an empty list
# XXX should not return empty (null string) list items

def getsubcol(row, column_name):
	col = getcol(row, column_name)
	if not col:
		return []
	return [s.strip() for s in col.split(':::')]

# slurp the content of CSV stream csvin into phonebook
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


# slurp the content of vCard stream vcardin into Grandstream phonebook
#
# skip vCards that:
# - have no phone number(s)
# - have no name or company name
# - aren't in our list of groups (labels) to include

def vcard_to_phonebook(vcardin, phonebook, incgroups, faves):
	import vcard

	reader = vcard.vCardReader(vcardin)
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

