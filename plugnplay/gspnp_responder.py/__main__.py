"""
Author: Bruce Walker <bruce.walker@gmail.com>
created: November, 2021

Copyright (c) 2021, Bruce Walker -- see the file LICENSE.
"""

if __name__ == "__main__":
	from sys import argv
	from gspnp_responder import main
	try:
		main(argv)
	except KeyboardInterrupt:
		...

