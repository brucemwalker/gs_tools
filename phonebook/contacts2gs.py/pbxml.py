"""
XML bits and pieces

Author: Bruce Walker <bruce.walker@gmail.com>
created: Nov 16, 2021

Copyright (c) 2021, Bruce Walker -- see the file LICENSE.
"""

import xml.etree.ElementTree as ET

# add a new text sub-element to an element <el><sub>text value</sub></el>

def el_addtext(element, name, text):
	new_element = ET.SubElement(element, name)
	new_element.text = text
	return new_element

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

