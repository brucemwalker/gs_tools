# Grandstream Plug and Play Responder
## Description

This application runs either standalone in a terminal window or as
a system daemon (background process). It listens for Grandstream
Plug and Play broadcasts from GRP26XX-series phones during every
boot process, logs details to stderr, and optionally responds with
a configuration URL that the phone will use to read config files
from.

## Environment

The application is written in pure Python3 and requires no extra
classes or libraries beyond the stock Python installation.

I developed and tested it under macOS 12 (Monterey) and FreeBSD
13.  I expect it will run without changes under pretty much any
flavour of macOS, BSD and Linux. It will most likely run in some
fashion under Windows if Python3 is installed, but don't hold me
to that.  I will test that later on.

On macOS you will possibly need to install a more recent Python than
the OS comes installed with. I recommend
[MacPorts](https://www.macports.org/)
for that.

## Command line options
```
% ./gspnp_responder -h
gspnp_responder [-vh] [url]
  -h   -- help; this message
  -v   -- verbose; extra debug stuff
  url  -- send configuration URL, eg http://192.168.1.2/gs/
          if no url, passively log beacons
```

A provided URL will be sent (in a SIP NOTIFY request) in response to
a SIP subscribe ua-profile event request from a Grandstream phone.
Grandstream stipulates that a valid URL must be a path with a trailing
slash and that the usual config files will be searched-for under
that path. Eg: `http://192.168.1.2/gs/`.
If you see URLs being sent to your phone but the phone is not configuring,
check your URL syntax first. The phone will silently ignore any URL sent it
that it doesn't like.

If no URL is provided it passively reports phone broadcasts as it 
sees them, but takes no other action.

One `-v` option will make `gspnp_responder` print a log when we send a profile
URL to a phone.
It will also report profile requests from other vendors besides
Grandstream, like Snom. (There's no support for sending profile URLs
to them though.)

Two `-v` options will enable some debugging output, like dumping the
entire packet contents of SIP subscribe and notify requests as well
as the SIP responses.

## Installation and use
### Standalone utility

You can launch `gspnp_responder` in a terminal window where it will
run until killed (eg control-C). Run without arguments it passively
displays the details of any GRP26XX series phone it sees booting.

Eg:
```
% ./gspnp_responder
Sun Dec  5 15:13:08 2021 | SUBSCRIBE mac:c074ad515e41 192.168.1.2 Grandstream GRP2612W fw 1.0.5.67
```

### System daemon

For use as a permanent system service, `gspnp_responder` is designed to be
managed by [supervisor](http://supervisord.org/).

Copy the application executable `gspnp_responder` to a system directory.
On FreeBSD I suggest `/usr/local/sbin`. Make sure it's set to be
executable.
```
% sudo cp gspnp_responder /usr/local/sbin
% sudo chmod 755 /usr/local/sbin/gspnp_responder
```

Add appropriate lines to the `supervisord.conf` configuration file:
```
; Grandstream Plug and Play responder

[program:gspnp_responder]
command=/usr/local/sbin/gspnp_responder -v http://192.168.1.2/gs/grp/
stderr_logfile=/var/log/gspnp_responder
```

Update supervisor:
```
% sudo supervisorctl update all
% sudo supervisorctl status
gspnp_responder                  RUNNING   pid 6960, uptime 0:00:06
nginx                            RUNNING   pid 4706, uptime 1 day, 1:37:39
```

## Usage notes
### Network considerations
The Grandstream "Plug and Play" protocol makes use of the SIP
protocol for discovering a user-agent profile. This involves the
client (eg phone) broadcasting (multicast UDP) a SIP *subscribe request*
for the *ua-profile event* to the local network.  Generally broadcasts
like this do not propagate beyond the subnet that the phone is
connected to. This of course means that `gspnp_responder` must
be running on a host on the same subnet as the phones it will
auto-configure.

### Zero-config
I was moved to create this application because configuring a brand
new or factory-reset
[GRP2612W](https://www.grandstream.com/products/ip-voice-telephony/carrier-grade-ip-phones/grp-series-professional-ip-phones/product/grp2612-p-w?hsLang=en)
phone for WiFi on my home office network is a decided
pain in the butt. Programming the WiFi settings--especially the
shared secret--using just the phone keyboard is *really* annoying.

So my procedure now is to run an instance of `gspnp_responder` on
a laptop or mini-PC with an ethernet port and a web server
(like the opensource [nginx](https://nginx.org/)).
Then I temporarily connect the GRP2612W phone with a CAT-5 patch
cable to the laptop and reboot it.  The phone will send its beacon,
`gspnp_responder` will send back the configuration URL (through a
SIP NOTIFY ua-profile event message) and the phone will read a
configuration file from the dedicated web server on the laptop.
That configuration file will contain values to program the WiFi
settings so that once the phone reboots it will be on my office
WiFi network where I can connect to it to finish setup.

Some example p-values are:
```
# HTTP access (Chrome dislikes the self-signed cert)
P1650 = 1
# enable WiFi
P7800 = 1
# AP #1 SSID string
P8403 = Wi-Fi_Name
# AP #1 shared secret
P8404 = Password
# Security type WPA/WPA2 PSK
P8405 = 4
```

If you convert these to Grandstream XML--you can use my `pvalues2xml`
conversion tool in this package; see
[Provisioning](https://github.com/brucemwalker/gs_tools/tree/main/provisioning)
--you'll get:
```
% pvalues2xml.py GRP261X.txt | xmllint --format -
<?xml version="1.0" encoding="UTF-8"?>
<gs_provision version="1">
  <!--Generated by /Users/bmw/bin/pvalues2xml.py-->
  <config version="1">
    <!-- HTTP access (Chrome dislikes the self-signed cert)-->
    <P1650>1</P1650>
    <!-- enable WiFi-->
    <P7800>1</P7800>
    <!-- AP #1 SSID string-->
    <P8403>Wi-Fi_Name</P8403>
    <!-- AP #1 shared secret-->
    <P8404>Password</P8404>
    <!-- Security type WPA/WPA2 PSK-->
    <P8405>4</P8405>
  </config>
</gs_provision>
```

Save that in a file called `cfg.xml` in the web server and all
GRP26XX phones will read it.

## See also

[Supervisor: A Process Control System](http://supervisord.org/)

[Auto-configuration “Plug and Play” Guide [PDF]](https://www.grandstream.com/hubfs/Product_Documentation/GRP2600_Plug_and_Play_Guide.pdf?hsLang=en)

[rfc6080 - A Framework for Session Initiation Protocol User Agent Profile Delivery](https://datatracker.ietf.org/doc/html/rfc6080)

[rfc3261 - SIP: Session Initiation Protocol](https://datatracker.ietf.org/doc/html/rfc3261)

[Grandstream GRP Series of Professional IP Phones](https://www.grandstream.com/products/ip-voice-telephony/carrier-grade-ip-phones?hsLang=en)

## Fine Print

Copyright (c) 2021, Bruce Walker -- see the file
[LICENSE](https://github.com/brucemwalker/gs_tools/blob/main/LICENSE).

