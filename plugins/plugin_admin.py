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

import argparse
import os
import shlex
import sys
import time

from datetime	import	datetime

from common import const, mounts, utils
from common.locations import Locations
from common.pyni import Config

#from	common.utils	import	*
#module = get_module()
#exec(get_import(mod=module, from_=['utils']))
#try:
#	exec(get_import(mod=module, from_=['mounts'], import_=['CommandMount']))
#except ImportError, e:
#	print e

Command = Locations.Command

class GrantAdmin(Command):
	name = 'grant'
	rank = const.RANK_HIDDEN
	file = __file__

	grant_pass = 'BaconIsYummy'
	plugin_name = os.path.split(__file__)[1]
	plugin_name = os.path.splitext(plugin_name)[0]
	with Config(utils.get_module(), 'plugins', plugin_name) as ini:
		if 'grant_pass' not in ini:
			ini.grant_pass = grant_pass
		else:
			grant_pass = ini.grant_pass
		ini._comments['grant_pass'] = '# This is the password' \
			'that needs to be passed to !grant to grant the caller admin status.'

	@classmethod
	def thread(self, bot):
		user, args = yield

		if args == self.grant_pass:
			with Config(utils.get_module(), 'roster') as roster:
				roster[utils.getname(user).lower()].rank = const.RANK_ADMIN
			bot.sendto(user, "You've been granted Admin status.")


class RawMsg(Command):
	name = 'raw'
	rank = const.RANK_ADMIN
	file = __file__

	@classmethod
	def thread(self, bot):
		user, args = yield

		bot.sendtoall(args)


class Whisper(Command):
	name = 'sm'
	rank = const.RANK_ADMIN
	file = __file__

	@classmethod
	def thread(self, bot):
		user, args = yield

		target, msg = utils.split_target(args)
		bot.sendto(target, msg)


class ToggleCommand(Command):
	name = 'toggle'
	rank = const.RANK_ADMIN
	file = __file__

	__doc__ = 'Disabled a command without unloading the whole plugin. \n' \
				'Usage: !toggle cmd_name'

	@classmethod
	def thread(self, bot):
		user, names = yield

		for name in names.split(','):
			name = name.strip()
			cmd = self.hooks.get(name)
			if not cmd:
				bot.sendto(user, "Unknown Command: %s" % name)
				return

			if cmd.rank == const.RANK_DISABLED:
				bot.sendto(user, 'Command Enabled: %s' % name)
				cmd.rank = cmd.prev_rank
				del cmd.prev_rank
			else:
				bot.sendto(user, 'Command Disabled: %s' % name)
				cmd.prev_rank = cmd.rank
				cmd.rank = const.RANK_DISABLED


class ForgetUser(Command):
	name = 'forget'
	rank = const.RANK_ADMIN
	file = __file__

	__doc__ = "Remove a user's information from the roster"

	@classmethod
	def thread(self, bot):
		user, args = yield

		with Config(utils.get_module(), 'roster') as roster:
			args = args.lower()
			if args in roster.keys():
				del roster[args]
				bot.sendto(user, 'Removed %s from the roster' % args)
			else:
				bot.sendto(user, 'Unknown User: %s' % args)


class HookIgnoreUser(Locations.EvMsg):
	name = 'ignore'
	#loc = [const.LOC_EV_MSG]
	file = __file__

	@classmethod
	def thread(self, bot):
		while True:
			user, msg = yield
			with Config(utils.get_module(), 'roster') as roster:
				if 'blocked' in roster[utils.getname(user).lower()]:
					yield True
					continue

			yield False


class IgnoreUser(Command):
	name = 'ignore'
	rank = const.RANK_ADMIN
	file = __file__

	__doc__ = "Make the bot ignore imput from the user. \n Usage: !ignored <username>"

	@classmethod
	def thread(self, bot):
		user, target = yield

		with Config(utils.get_module(), 'roster') as roster:
			unix_target = target.lower()
			if roster.has_key(unix_target):
				if roster[unix_target].has_key('ignored'):
					bot.sendto(user, "%s is already ignored." % target)
				else:
					roster[unix_target].ignored = True
					bot.sendto(user, "I am no longer accepting input from %s." % target)
			else:
				roster[unix_target].ignored = True
				bot.sendto(user, "I am no longer accepting input from %s. NOTE: I don't know who that is." % target)


class UnignoreUser(Command):
	name = 'unignore'
	rank = const.RANK_ADMIN
	file = __file__

	__doc__ = "Allow the user to interact with the bot. \n Usage: !unignored <username>"

	@classmethod
	def thread(self, bot):
		user, target = yield

		with Config(utils.get_module(), 'roster') as roster:
			unix_target = target.lower()
			if roster.has_key(unix_target):
				if not roster[unix_target].has_key('ignored'):
					bot.sendto(user, "%s is not ignored." % target)
				else:
					del roster[unix_target].ignored
					bot.sendto(user, "I am now accepting input from %s." % target)
			else:
				bot.sendto(user, "I don't know who %s is, therefore they cannot have been ignored." % target)
