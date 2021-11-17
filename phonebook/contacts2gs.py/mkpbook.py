#!/usr/bin/env python3

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
"""

BRIEF = 'usage: goog2gs [-hfP] [-F faves] [-g inc-group [...]] [-o xml-file] [csv-file [...]]'

HELP = f'''{BRIEF}

Convert Google Contacts CSV or vCard export files into Grandstream phonebook
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

Additional arguments are read in order for contact files to include.
Standard input is read in the absence of args.

If no -g options or a -f option are specified all contacts found
in the given files are included in the phonebook output.

If a -f or one or more -g options are given then only contacts
which are members of that group list are included in the phonebook
output.
'''

DEFAULT_FAVES = 'Starred'

"""
Grandstream GRP26xx screws up dialing and phonebook editing
with any formating chars at all in the phone numbers.
    "Number is required and must only contain DTMF digits"
Set ENABLE_PRETTYPRINT=True to allow some formatting anyway.
-P   - enable pretty-print
"""

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
 https://www.grandstream.com/hubfs/Product_Documentation/GXP_XML_phonebook_guide.pdf
"""

def stats(d={}):
	print(f'{d['seen']} contacts seen\n{d['imported']} contacts imported')

def main(argv):
	from contacts import csv_to_phonebook, vcard_to_phonebook, GSTARRED
	import pbxml
	import xml.etree.ElementTree as ET
	import sys, getopt, os.path

	out = sys.stdout
	incgroups = []
	faves = DEFAULT_FAVES
	ftype = 'csv'
	verbose = False

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
			incgroups += [GSTARRED]
		elif opt == '-g':
			incgroups += [arg]
		elif opt == '-t':
			ftype = arg
		elif opt == '-F':
			faves = arg
		elif opt == '-v':
			verbose = True

	addrbook = ET.Element('AddressBook')
	pbxml.el_addtext(addrbook, 'version', '1')
	pbxml.get_or_insert_group(addrbook, faves)

	if not args:
		stats = csv_to_phonebook(sys.stdin, addrbook, incgroups, faves)
		if verbose: pstats(stats)
	else:
		for csvfile in args:
			if not os.path.isfile(csvfile):
				print(f'{csvfile}: not found', file=sys.stderr)
				continue
			with open(csvfile, newline='') as cf:
				stats = csv_to_phonebook(cf, addrbook, incgroups, faves)
				if verbose: pstats(stats)

	# create the Grandstream-formatted XML phonebook

	with sys.stdout if out==sys.stdout else open(out, 'w') as f:
		f.write('<?xml version="1.0" encoding="UTF-8"?>')
		f.write(ET.tostring(addrbook, encoding="unicode"))

if __name__ == "__main__":
	from sys import argv
	main(argv)

