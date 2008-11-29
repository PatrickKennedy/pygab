#!/usr/bin/env python

from	common	import	utils
try:
	exec(utils.get_import(mod=utils.get_module(),
						  from_=['mounts'], import_=['*']))
except ImportError, e:
	raise
