# gs_tools
## Grandstream VoIP device utilities

Tools to support using and administrating Grandstream Networks IP-phones and ATA's. 

### Phonebook
- convert Google Contacts CSV and Apple macOS vCard export files into Grandstream Phonebook XML compatible with the GRP26XX Carrier Grade (and possibly GXPxxxx) IP phones

### Provisioning
- convert P-values to XML format files suitable for manual or automatic fetching
- convert XML format back to P-values

### Discovery
- view provisioning beacons

### Ringtones
- some reasonably decent recordings of vintage terminals and business phones as alternatives to the factory installed ones.

### Hints, How-Tos
- cheat-sheet for using SoX to convert Grandstream ringtones, adjust the volume of existing ones, etc.
- some advice on connecting and using the GRP26XX devices in a Small Office / Home Office environment.
- basic P-values to get your device connected to voip.ms fast.

## What you need

- The command-line tools require a recent-ish Python 3 to be installed.
- Tested on FreeBSD and macOS.

## Motivation

I began building and collecting these tools and ancillary stuff
after I bought a Grandstream GRP2612W.  I was taken right away by
how much this device in particular is The Perfect Home Office Phone
that I wish I had years ago. It's very flexible, nicely styled,
and, with its built-in WiFi, completely portable.

But this product feels like it targets the larger scale deployment
where you'd expect to find full-time IT staff using a management
console.  As such it is not very end-user "consumer friendly". It's
also missing some niceties like professional-sounding ringtones.

So as I uncovered little shortcomings that I figured I could do
something about myself I began to work on them, starting with
Provisioning.

## See Also

Grandstream Phonebook XML syntax - https://www.grandstream.com/hubfs/Product_Documentation/gxv33xx_xml_phonebook_guide.pdf?hsLang=en

rfc2426 - vCard MIME Directory Profile [version 3.0] - https://datatracker.ietf.org/doc/html/rfc2426



## Fine Print

Copyright (c) 2021, Bruce Walker -- see the file LICENSE.

