"""
eventloop.py -- manage the app event loop

- support selector read/write events and callbacks
  - selector.register()

- support timers based on sched
  - scheduler.enter(), enterabs(), cancel()
  - one second granularity

- use an open socket for rx/tx
  - socket.recvfrom(bufsize)
  - socket.sendto(bytes, address)

- use a queue for output buffering (to avoid blocking)
  - suggested for message passing
  - q = queue.SimpleQueue()
    q.put_nowait(item)
    q.empty()
    item = q.get_nowait()

https://docs.python.org/3/library/selectors.html?#selectors.DefaultSelector
https://docs.python.org/3/library/sched.html#sched.scheduler.enter
https://docs.python.org/3/library/socket.html#socket.socket.recvfrom
https://docs.python.org/3/library/queue.html

Author: Bruce Walker <bruce.walker@gmail.com>
created: November, 2021

Copyright (c) 2021, Bruce Walker -- see the file LICENSE.
"""

import sched
import selectors
import time

"""
Python will run these once on the first import; they will then be
global, static variables

The app's main() should call run() after initial setup, eg: file
objects are registered with selector.
"""

selector = selectors.DefaultSelector()
scheduler = sched.scheduler(time.time)	# XXX float val may cause creepage

def run():
	global selector, scheduler

	while True:
		for key, mask in selector.select(1):
			key.data(key.fileobj, mask)
		scheduler.run(blocking=False)

