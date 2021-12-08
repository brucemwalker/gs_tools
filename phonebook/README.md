# Phonebook conversion tool
## Description
Convert Google Contacts and macOS Contacts.app export files to Grandstream
Addressbook XML format for use with Grandstream phones.

## Who is this for?
Grandstream GRP26XX-series phones support uploaded phonebooks for
dialing assistance and to display name lookups for incoming calls.
But they expect a proprietary XML format which is only supported
by their own
[enterprise PBX systems](https://www.grandstream.com/products/ip-pbxs/ucm-series-ip-pbxs).
Small Office / Home Office
(SOHO) and non-enterprise users are left out, so I made this tool.

It reads one or more phonebook files and writes contacts to a single
Grandstream XML file.  It understands Google Contacts (both CSV and
vCard) and Apple's macOS Contacts.app vCard formats.

## Features
- you can control which Google Contacts tags to include in the import. They are saved in Grandstream phonebook "groups". If you don't specify, all contacts with phone numbers are imported.
- Starred contacts are listed when dialing
  and appear in a Starred tab of the Groups menu.
- unique ringtones per-contact are supported through Google contacts (only with Google Contacts)

### Unique ringtones per contact
  - edit a contact you want to set a ringtone for.
  - using a Custom Field, set the value to one of:
     `default ringtone`, `system`, `silent`, `ring1.bin`, ... etc.
  - set the Label to `Ringtone`

## Preparing input contact files
The app reads CSV and vCard files from Google Contacts and also vCard files
from Apple macOS Contacts.app.
It can be told what the format is but by default it figures that
out for itself.

I recommend using CSV format when exporting from Google Contacts because 
I support more features with that format.

### Exporting contacts from Google Contacts
1. click on `Export` from the left-hand column, below Labels.
2. choose `Export as Google CSV` in the pop-up menu.
3. click `Export`.

### Exporting contacts from Apple macOS Contacts.app
1. select a contact, group of contacts or All contacts
2. Navigate to File -> Export -> Export vCard...

## Environment
This command-line application is written in pure Python3 and requires
no extra classes or libraries beyond the stock Python installation.

I developed and tested it under macOS 12 (Monterey) and FreeBSD 13.
I expect it will run without changes under pretty much any flavour
of macOS, BSD and Linux. It runs under Windows if Python3 is
installed (Windows 11 tested).
Get the Windows installer from here: [Download Windows installer (64-bit)](https://www.python.org/downloads/windows/).
Also rename `contacts2gs` to `contacts2gs.py`.

On macOS you might possibly need to install a more recent Python than
the OS comes installed with. I recommend installing 
[MacPorts](https://www.macports.org/)
for that.

## Command line options
```
% ./contacts2gs -h
usage: goog2gs [-hfPv] [-F faves] [-g inc-group [...]] [-o xml-file] [-t "vcard|csv"] [csv-file [...]]

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
```

## Usage examples
In the usual case we have a Google Contacts export called `contacts.csv`:
```
% ./contacts2gs -o contacts.xml contacts.csv
```
As above, but only include contacts in tagged `Neighbors` and `Vendors`:
```
% ./contacts2gs -g Neighbors -g Vendors -o contacts.xml contacts.csv
```
As above but in addition include all the *starred* contacts (`-f`):
```
% ./contacts2gs -f -g Neighbors -g Vendors -o contacts.xml contacts.csv
```
To pretty-print the output, pipe the output from contacts2gs through
an XML utility such as `xmllint` (macOS). Example:
```
% ./contacts2gs -f -g Neighbors -g Vendors contacts.csv | xmllint --format contacts.xml > fmt_contacts.xml
```

## References
- [Grandstream Phonebook XML syntax](https://www.grandstream.com/hubfs/Product_Documentation/gxv33xx_xml_phonebook_guide.pdf?hsLang=en)
- [rfc2426 - vCard MIME Directory Profile [version 3.0]](https://datatracker.ietf.org/doc/html/rfc2426)

## Fine Print

Copyright (c) 2021, Bruce Walker -- see the file [LICENSE](../LICENSE).

