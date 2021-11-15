#!/usr/bin/env python3

# convert Grandstream p-values to GS version-1 XML
#
# Author: Bruce Walker <bruce.walker@gmail.com>
# modified: Nov 7, 2021
# created: Nov 5, 2021

# Usage:
#   pvalues2xml.py [-c] [-o config.xml] [-m mac] [config.txt [...]]
# Simple:
#   pvalues2xml.py < config.txt > config.xml
# Pretty XML:
#   pvalues2xml.py < config.txt | xmllint --format - > config.xml

# To-Do

import xml.etree.ElementTree as ET
from re import match, sub
import os.path, sys, getopt

# refs
#  https://docs.python.org/3/library/xml.etree.elementtree.html
# comments
# https://docs.python.org/3.9/library/xml.etree.elementtree.html#xml.etree.ElementTree.Comment
# ordering
# https://docs.python.org/3.9/library/xml.etree.elementtree.html#xml.etree.ElementTree.canonicalize
# https://docs.python.org/3/library/getopt.html

class Syntax(Exception): pass
class Comment(Exception): pass

# add a new text sub-element to an element <el><sub>text value</sub></el>

def el_addtext(element, name, text):
	new_element = ET.SubElement(element, name)
	new_element.text = text
	return new_element

# slurp open file dscriptor p-value pvaluefile into config element

def add_pvalues(pvaluefile, config, comments=True):
	for s in pvaluefile:
		try:
			s = s.strip()
			if not s:
				raise(Comment)			# blank line
			if s[0] == '#':
				s = s.lstrip('#')
				raise(Comment)			# hash comment
			p, val = s.split('=', 1)	# exception if malformed
			p, val = p.strip(), val.strip()
			if not match('P[0-9]+$', p):
				raise(Syntax)			# invalid p-value
		except (Comment, Syntax, ValueError):
			if comments:
				config.append(ET.Comment(s))
		else:
			el_addtext(config, p, val)

def macclean(s):
	mac = sub('[^0-9a-f]', '', s.lower())
	if len(mac) == 12:
		return mac
	else:
		print(f'warning: invalid MAC address {s}', file=sys.stderr)
		return s

def main(argv):
	brief = 'pvalues2xml [-c] [-o cfg.xml] [-m mac] [pvals.txt [...]]'
	mac = ''
	out = sys.stdout
	comments = True

	try:
		opts, args = getopt.getopt(argv, "hcm:o:")
	except getopt.GetoptError:
		print(brief, file=sys.stderr)
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print(brief)
			sys.exit()
		elif opt == '-c':
			comments = False
		elif opt == '-m':
			mac = macclean(arg)
		elif opt == '-o':
			out = arg

	configxml = ET.Element('gs_provision', version='1')
	if comments:
		configxml.append(ET.Comment(f'Generated by {sys.argv[0]}'))
	if mac:
		el_addtext(configxml, 'mac', mac)
	cfg = ET.SubElement(configxml, 'config', version='1')

	if not args:
		add_pvalues(sys.stdin, cfg, comments)
	else:
		for pfile in args:
			if not os.path.isfile(pfile):
				print(f'{pfile}: not found', file=sys.stderr)
				continue
			with open(pfile) as pf:
				add_pvalues(pf, cfg, comments)

	# create the Grandstream-formatted XML config file

	with sys.stdout if out==sys.stdout else open(out, 'w') as f:
		f.write('<?xml version="1.0" encoding="UTF-8"?>')
		f.write(ET.tostring(configxml, encoding="unicode"))

if __name__ == "__main__":
	main(sys.argv[1:])

