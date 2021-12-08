"""
convert Google Contacts CSV or vCard file to Grandstream Addressbook XML

- export from Google Contacts; use Google CSV format from All contacts

- export from Apple macOS Contacts.app; select a contact, group of contacts
  or All contacts; File -> Export -> Export vCard...

Author: Bruce Walker <bruce.walker@gmail.com>
created: Nov 16, 2021

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
- in pbgroup spec, what does <Primary> do?

Implementation notes:
- GS phonebook contacts _must_ have:
  - a last name
  - at least one phone number
  - numbers may contain formating, but no trailing extension, etc.
    - stick to hyphens; brackets & spaces are questionable

refs
 https://www.grandstream.com/hubfs/Product_Documentation/GXP_XML_phonebook_guide.pdf
"""

BRIEF = 'usage: goog2gs [-hfPv] [-F faves] [-g inc-group [...]] [-o xml-file] [-t "vcard|csv"] [csv-file [...]]'

HELP = f'''{BRIEF}

Convert Google Contacts CSV or vCard export files into Grandstream phonebook
XML records.

  -g pbgroup
          create a phonebook group 'pbgroup' and include contacts
          with this label in it.
          Every -g option adds another group.
  -f      include 'starred' contacts (faves) in a group
          called 'Starred' by default.
  -F name
          replace the default faves group name.
  -o xmlfile
          write Grandstream phonebook XML to 'xmlfile'.
          Output is written to standard output if this
          option is missing.
  -h      help (this text).
  -t ftype
          files will be expected to be of specified type,
		  which should be one of 'csv' or 'vcard'.
		  By default we make an educated guess for each file,
		  falling back on CSV as a last resort.
  -v      verbose; write stats, comments to stderr

Additional arguments are read in order for contact files to include.
Standard input is read in the absence of args.

If no -g options or a -f option are specified all contacts found
in the given files are included in the phonebook output.

If a -f or one or more -g options are given then only contacts
which are members of that group list are included in the phonebook
output.
'''

'''
Grandstream GRP26xx screws up dialing and phonebook editing
with any formating chars at all in the phone numbers.
    "Number is required and must only contain DTMF digits"
Set ENABLE_PRETTYPRINT=True to allow some formatting anyway.
-P   - enable pretty-print
'''

DEFAULT_FAVES = 'Starred'


# XXX would it better to spelunk the phonebook XML object?
#     yes; yes it would.

def pstats(d={}, verbosity=0):
	import sys

	if verbosity < 1:
		return
	nm = d.get('name','?')
	t, i, n = d.get('seen','0'), d.get('imported','0'), d.get('numbers','0')

	print(f'{nm}:', file=sys.stderr)
	print(f"  {t} contacts seen\n  {i} contacts imported", file=sys.stderr)

	if verbosity < 2:
		return
	print(f"  {n} numbers imported", file=sys.stderr)


def main(argv):
	import contacts as CT
	import pbxml
	import xml.etree.ElementTree as ET
	import sys, getopt, os.path

	faves = DEFAULT_FAVES
	ftype = ""
	incgroups = []
	out = sys.stdout
	verbosity = 0

	try:
		opts, args = getopt.getopt(argv[1:], "hfPvF:g:o:t:")
	except getopt.GetoptError:
		print(BRIEF, file=sys.stderr)
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print(HELP)
			sys.exit()
		elif opt == '-P':
			pp = True
		elif opt == '-o':
			out = arg
		elif opt == '-f':
			incgroups += [CT.GSTARRED]
		elif opt == '-g':
			incgroups += [arg]
		elif opt == '-t':
			ftype = arg
		elif opt == '-F':
			faves = arg
		elif opt == '-v':
			verbosity += 1

	addrbook = ET.Element('AddressBook')
	pbxml.el_addtext(addrbook, 'version', '1')
	pbxml.get_or_insert_group(addrbook, faves)

	if not args:
		if not ftype:
			ftype = CT.sniff(sys.stdin)
		if ftype == 'csv':
			stats = CT.csv_to_phonebook(sys.stdin, addrbook, incgroups, faves)
		elif ftype == 'vcard':
			stats = CT.vcard_to_phonebook(sys.stdin, addrbook, incgroups, faves)
		else:
			print('unrecognized contact format', file=sys.stderr)
			return		# XXX exit
		pstats(stats, verbosity)
	else:
		for ctfile in args:
			if not os.path.isfile(ctfile):
				print(f'{ctfile}: not found', file=sys.stderr)
				continue
			with open(ctfile, newline='', encoding='utf-8') as cf:
				ft = ftype if ftype else CT.sniff(cf)
				if ft == 'csv':
					stats = CT.csv_to_phonebook(cf, addrbook, incgroups, faves)
				elif ft == 'vcard':
					stats = CT.vcard_to_phonebook(cf, addrbook, incgroups, faves)
				else:
					print(f'{ctfile}: unrecognized contact format',
						file=sys.stderr)
					continue
				pstats(stats, verbosity)

	# create the Grandstream-formatted XML phonebook

	with sys.stdout if out==sys.stdout else open(out, 'w') as f:
		f.write('<?xml version="1.0" encoding="UTF-8"?>')
		f.write(ET.tostring(addrbook, encoding="unicode"))

