# Grandstream Plug and Play Responder
## Description

This application runs either standalone or as a system daemon
(background process). It watches for Grandstream Plug and Play
broadcasts from GRP26XX-series phones during every boot process,
logs details to stderr, and optionally responds with a configuration
URL that the phone will use to read config files from.

## Environment

The application is written in pure Python3 and requires no extra
classes or libraries beyond the stock Python installation.

It was developed and tested under macOS 12 (Monterey) and FreeBSD
13.  I expect it will run without changes under pretty much any
flavour of macOS, BSD and Linux. It will most likely run in some
fashion under Windows if Python3 is installed, but don't hold me
to that.  I will test that later on.

On macOS you will possibly need to install a more recent Python than
the OS comes with. See [MacPorts](https://www.macports.org/) for that.

## Command line arguments
```
% ./gspnp_responder -h
gspnp_responder [-vh] [url]
  -h   -- help; this message
  -v   -- verbose; extra debug stuff
  url  -- send configuration URL, eg http://192.168.1.2/gs/
          if no url, passively log beacons
```

## Installation and use
### Standalone utility

You can launch gspnp_responder in a terminal window where it will
run until killed (eg control-C). Run without arguments it passively
displays the details of any GRP26XX series phone it sees booting.

Eg:
```
% gspnp_responder
Sun Dec  5 15:13:08 2021 | SUBSCRIBE mac:c074ad515e41 192.168.1.2 Grandstream GRP2612W fw 1.0.5.67
```

### System daemon

For use as a permanent system service, gspnp_responder is designed to be
managed by [supervisor](http://supervisord.org/)

Copy the application file gspnp_responder to a system directory.
On FreeBSD I suggest `/usr/local/sbin`. Make sure it's set to
executable.
```
% sudo cp gspnp_responder /usr/local/sbin
% sudo chmod 755 /usr/local/sbin/gspnp_responder
```

Add appropriate lines to a supervisor `.ini` file:
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
gspnp_responder                  RUNNING   pid 6960, uptime 0:50:06
nginx                            RUNNING   pid 4706, uptime 1 day, 1:37:39
```

## See Also

[Supervisor: A Process Control System](http://supervisord.org/)

[Auto-configuration “Plug and Play” Guide [PDF]](https://www.grandstream.com/hubfs/Product_Documentation/GRP2600_Plug_and_Play_Guide.pdf?hsLang=en)

[rfc6080 - A Framework for Session Initiation Protocol User Agent Profile Delivery](https://datatracker.ietf.org/doc/html/rfc6080)

[rfc3261 - SIP: Session Initiation Protocol](https://datatracker.ietf.org/doc/html/rfc3261)

