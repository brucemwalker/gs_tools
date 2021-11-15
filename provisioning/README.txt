Grandstream Provisioning Notes
==============================

Peculiarities
-------------

- the GRP2612W only accepts P-values via the web admin UI:
    Maintenance -> Upgrade and Provisioning -> Upload Device Configuration

- the GRP2612W accepts XML (v1,v2) but not P-values via the Config server:
  cfgffeeddccbbaa.xml
  cfggrp2612w.xml
  cfg.xml
  devc074ad53085a.cfg	# XXX double-check this!

- the XML seems robust and compliant.

- it also accepts the old original binary format, apparently. Not tested.
  cfgffeeddccbbaa


Format versions
---------------

  - P-values  eg:
    P3=Bruce Walker
    P35=654321_ph2-ln1

  - XML version 1  eg:
    <gs_provision version="1">
        <config version="1">
            <P3>Bruce Walker</P3>
            <P35>654321_ph2-ln1</P35>

  - XML version 2  eg:
    <gs_provision>
        <config version="2">
            <item name="account.1.sip.subscriber">
                <part name="name">Bruce Walker</part>
                <part name="userid">654321_ph2-ln1</part>
            </item>

  - binary, unversioned(?) proprietary (requires GS tools)


