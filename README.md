# gs_tools
## Grandstream VoIP device utilities
Tools to support using and administrating Grandstream Networks
IP-phones and ATA's.

### Phonebook
- convert Google Contacts CSV and Apple macOS vCard export files into Grandstream Phonebook XML compatible with the GRP26XX Carrier Grade (and possibly GXPxxxx) IP phones

### Provisioning
- convert P-values to XML format files suitable for manual or automatic fetching
- convert XML format back to P-values [TBD]

### Plug and Play / Discovery
- view provisioning beacons from booting-up phones
- return a configuration URL to the phones, or not

Applies to the GRP26XX Carrier Grade series. Could be hacked to
support Snom, likely others.

### Ringtones
- some reasonably decent recordings of vintage terminals and business phones as alternatives to the factory installed ones. [TBD]

### Hints, How-Tos
- some advice on connecting and using the GRP26XX devices in a Small Office / Home Office environment.
- cheat-sheet for using SoX to convert Grandstream ringtones, adjust the volume of existing ones, etc. [TBD]
- basic P-values to get your device connected to voip.ms fast. [TBD]

## What you need
- The command-line tools require a recent-ish Python3 to be installed.
- Tested on FreeBSD and macOS.
- Should work fine on Linux flavours, and adaptable to Windows.

## Motivation
I began building and collecting these tools and ancillary stuff
after I bought a Grandstream GRP2612W.  I was taken right away by
how much this device in particular is The Perfect Home Office Phone
that I wish I had years ago. It's very flexible, nicely styled, has
excellent sound, and, with its built-in WiFi, is completely portable.

But this product feels like it targets the larger scale enterprise
or corporate deployment where you'd expect to find full-time IT
staff using a management console.  As such it is not very end-user
"consumer friendly". It's also missing some niceties like
a larger choice of ringtones.

So as I uncovered little shortcomings that I figured I could do
something about myself I began to work on them, starting with
Provisioning.

## See Also
- [Grandstream GRP Series carrier-grade phones](https://www.grandstream.com/products/ip-voice-telephony/carrier-grade-ip-phones)

## Fine Print

Copyright (c) 2021, Bruce Walker -- see the file [LICENSE](LICENSE).

*Also, I have absolutely no connection with Grandstream--I just like their
VoIP products.*

