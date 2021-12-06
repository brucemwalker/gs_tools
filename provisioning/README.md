# Grandstream P-Values to XML converter
## Description
Convert Grandstream `p-value` provisioning rules into 
`XML` format for configuring Grandstream IP-phones and ATA's.

## Who is this for?
Grandstream VoIP devices (ATAs and IP-phones) have traditionally
been provisionable by uploading text files containing `p-values`,
short *key*=*value* strings like this:
```
# Account Active: Yes
P271=1

# Account Name:
P270=1212

# SIP Server:
P47=montreal17.voip.ms
```

But Grandstream product firmware has increasingly been making use
of XML format files for provisioning. Files of one format or another
can be uploaded directly through a web interface or fetched by the
product during booting typically from TFTP or HTTP servers.

Sadly, while both `p-values` and `XML` files are accommodated through the
web interface, TFTP/HTTP boot-time fetches only support XML. So
you can use this converter to turn your `p-value` files into `XML` files.

## Features
- the converter by default preserves comments found in the p-value files
  and inserts them in order as XML-comments.
  Suppress the comments with `-c`
- include a distinguishing ethernet MAC address in the XML file with
  `-m mac-address`. The filter recognizes colon-separated values
  as well as just plain 12 hex digits.

## Command line options
```
% pvalues2xml.py -h
pvalues2xml [-c] [-o cfg.xml] [-m mac] [pvals.txt [...]]
```

## Usage examples
### Simple
Convert p-values in pvalues.txt to XML in cfg.xml:
```
% pvalues2xml.py -o cfg.xml pvalues.txt
```
### Pretty
As above but with pretty XML:
```
% pvalues2xml.py pvalues.txt | xmllint --format - > cfg.xml
```
### Include a MAC address
Add an ethernet MAC address along with the XML in cfg.xml:
```
% pvalues2xml.py -m 001122AABBCC -o cfg.xml pvalues.txt
```

## Environment
This command-line application is written in pure Python3 and requires
no extra classes or libraries beyond the stock Python installation.

I developed and tested it under macOS 12 (Monterey) and FreeBSD
13.  I expect it will run without changes under pretty much any
flavour of macOS, BSD and Linux. It will most likely run in some
fashion under Windows if Python3 is installed, but don't hold me
to that.  I will test that later on.

On macOS you might possibly need to install a more recent Python than
the OS comes installed with. I recommend installing 
[MacPorts](https://www.macports.org/)
for that.

### Installing
To *install* it, just copy the Python executable to somewhere in your shell's
search path, like the `bin` folder in your home directory.
```
% cp pvalues2xml.py ~/bin
```

## See also
- [SIP Device Provisioning Guide](https://www.grandstream.com/hubfs/Product_Documentation/gs_provisioning_guide.pdf) - more information on p-values, XML format, and device boot-time provisioning protocol.
- [Grandstream Tools](https://www.grandstream.com/support/tools) - Grandstream-provided tools and scripts.

## Fine Print

Copyright (c) 2021, Bruce Walker -- see the file [LICENSE](../LICENSE).

