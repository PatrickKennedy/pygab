#!/usr/bin/env python
#
#  PyGab - Python Jabber Framework
#  Copyright (c) 2008, Patrick Kennedy
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#
#  - Redistributions of source code must retain the above copyright
#  notice, this list of conditions and the following disclaimer.
#
#  - Redistributions in binary form must reproduce the above copyright
#  notice, this list of conditions and the following disclaimer in the
#  documentation and/or other materials provided with the distribution.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE FOUNDATION OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import	datetime
import	random
import	re
import	shlex
import	time

from	common			import argparse, const, mounts, utils
from	common.ini		import iMan

class Init(mounts.PluginInitializers):
	name = __file__

	def initialize(self):
		iMan.load([utils.get_module(), 'roster'])

	def __exit__(self, *args):
		iMan.unload('roster')
		mounts.PluginInitializers.remove(self.__class__)

class Search(mounts.CommandMount):
	name = 'search'
	rank = const.RANK_USER
	file = __file__

	__doc__ = """Search for users containing a passed arg.
Dan - Searches for all names containing 'dan'
*Dan - Searches for all names ending with 'dan'
Dan* - Searches for all names beginning with 'dan'"""

	def thread(self, user, sub, whisper):
		#if not self.parent.was_whispered and not utils.isadmin(user):
			#raise const.CommandHelp, 'Whisper Only Command'

		sub = sub.lower().encode('utf-8', 'replace')
		base = str

		if len(sub) < 3:
			raise const.CommandHelp, 'Minimum 3 Letters'

		if sub.startswith('*'):
			sub = sub[1:]
			func = base.endswith
		elif sub.endswith('*'):
			sub = sub[:-1]
			func = base.startswith
		else:
			func = base.count

		names = [name for name in iMan.roster if func(name, sub)]
		if names:
			reply = 'Matched Names (%s) - %s' % (len(names), ', '.join(names))
		else:
			reply = "I can't find anyone with your search parameters."

		if self.parent.was_whispered:
			self.parent.sendto(user, reply)
		else:
			self.parent.sendtoall(reply)
