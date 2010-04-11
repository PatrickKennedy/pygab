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
import	operator
import	random
import	re
import	shlex
import	threading

from	common			import argparse, const, mounts, utils
from	common.ini		import iMan

class Init(mounts.PluginInitializers):
	name = __file__

	def initialize(self):
		iMan.load([utils.get_module(), 'roster'])
		iMan.load([utils.get_module(), 'mail'])

	def __exit__(self, *args):
		iMan.unload('roster')
		iMan.unload('mail')
		mounts.PluginInitializers.remove(self.__class__)


def delay_hookmail():
	"""

	The bot may recieve online events when it comes online so we'll use a timer
	to ignore those.

	"""
	class HookMail(mounts.HookMount):
		name = 'mail'
		loc = [const.LOC_EV_ONLINE]
		file = __file__
		priority = const.PRIORITY_PERSISTANT

		def thread(self, user, status):
			username = utils.getname(user).lower()
			if username in iMan.mail:
				def f():
					self.parent.sendto(
						user, "You've got %d new messages. "
						"Please type '/w %s !mail get' to read it." %
						(len(iMan.mail[username].keys()), iMan.config.server.displayname)
					)
				self.parent.addTimer(1, f, 0, type='seconds')
				return
t = threading.Timer(10.0, delay_hookmail)
t.start()


class Mail(mounts.CommandMount):
	name = 'mail'
	rank = const.RANK_USER
	file = __file__

	arg_parser = argparse.ArgumentParser(prog='!mail', add_help=False)
	arg_parser.add_argument(
		'message',
		default=False, nargs='*',
		metavar='message', help='Mail message'
	)
	arg_parser.add_argument(
		'-g', '--get',
		action='store_true',
		help='Get the next message on your box'
	)
	arg_parser.add_argument(
		'-t', '--to',
		default=False, nargs='?',
		metavar='recipient', help='recipent of your message'
	)

	__doc__ = "Send a single message to a user next time they login. \n" \
				"Usage: !mail <get|check|username message> "

	def thread(self, user, args, whisper):
		if not args:
			raise const.CommandHelp
		args = args.split(' ', 1)
		cmd, message = args[0], args[1:]
		cmd = cmd.lower()
		username = utils.getname(user).lower()

		if cmd == 'get':
			if username in iMan.mail:
				letters = iMan.mail[username].items()
				# Only take the top letter.
				sender, message = letters[0]

				self.parent.sendto(user, "%s says '%s'" % (sender, message))
				self.parent.sendto(
					user, "You have %s more letter%s." %
						((len(letters) - 1) or 'no',
						((len(letters) - 1) != 1 and 's') or ''
					)
				)

				del iMan.mail[username][sender]
				if not iMan.mail[username]:
					del iMan.mail[username]
			else:
				self.parent.sendto(user, "I have no letters for you.")

		elif cmd == 'check':
			letters = len(iMan.mail.get(username, []))
			self.parent.sendto(
				user, 'I have %s letter%s for you.' % (
					letters or 'no',
					(letters != 1 and 's') or ''
				)
			)

		else:
			if not message:
				raise const.CommandHelp, "Missing message"
			target = cmd.lower()
			if target == iMan.config.server.displayname.lower():
				self.parent.sendto(user, "Why do you need to send me mail?")
				return
			elif target not in iMan.roster:
				self.parent.sendto(user, "I don't know %s and, therefore, "
								   "can't send him a letter." % cmd)
			else:
				iMan.mail[target][utils.getname(user)] = ' '.join(message)
				self.parent.sendto(user, "I have mailed your message to %s. "
								   "He will notified it when he logs in." % cmd)

		iMan.mail.save()
