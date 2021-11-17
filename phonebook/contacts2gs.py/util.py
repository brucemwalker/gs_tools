"""
utility bits and pieces

Author: Bruce Walker <bruce.walker@gmail.com>
created: Nov 16, 2021

Copyright (c) 2021, Bruce Walker -- see the file LICENSE.
"""

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

