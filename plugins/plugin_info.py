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
import datetime
import re
import shlex
import time

from common	import const, utils
from common.locations import Locations
from common.pyni import Config

Command = Locations.Command

class Help(Command):
	name = 'help'
	rank = const.RANK_USER
	file = __file__

	help_parser = argparse.ArgumentParser(prog='!help', add_help=False,
		epilog='''Options in <>'s are required.\n\
			Options in []'s are optional.\n\
			Don't include backets.''')
	help_parser.add_argument('cmd', const=True, nargs='?',
		metavar='command -', help='Display detailed information about a command.')

	__doc__ = """Display this help message.\n%s""" % (help_parser.format_help())

	@classmethod
	def thread(cls, bot):
		user, args = yield
		args = cls.help_parser.parse_args(shlex.split(args))
		if args.cmd:
			if args.cmd in Command.hooks:
				bot.sendto(user, Command.hook[args.cmd].__doc__)
			else:
				bot.error(user, "I don't know that command (%s)."
					" Please check your spelling." % args.cmd)
			return

		with Config(utils.get_module(), 'config') as config:
			reply = "Cmd Prefix: %s" % (config.system.commandprefix)

		lists = {
			const.RANK_USER: [],
			const.RANK_MOD: [],
			const.RANK_ADMIN: [],
			const.RANK_DISABLED: [],
			const.RANK_HIDDEN: [],
			const.RANK_BANNED: [],
		}
		for (name, cmd) in Command.activities.items():
			#TODO: Skip commands if a user doesn't match the command's rank.
			lists[cmd.rank].append(name)

		user_is_mod = utils.ismod(user)
		user_is_admin = utils.isadmin(user)

		reply += " | "
		reply += ', '.join(lists[const.RANK_USER])
		if lists[const.RANK_MOD] and (user_is_mod or user_is_admin):
			reply += '; '
			reply += ', '.join(lists[const.RANK_MOD])
		if lists[const.RANK_ADMIN] and user_is_admin:
			reply += '; '
			reply += ', '.join(lists[const.RANK_ADMIN])
		if lists[const.RANK_DISABLED] and (user_is_mod or user_is_admin):
			reply += " | Disabled: "
			reply += ', '.join(lists[const.RANK_DISABLED])

		bot.sendto(user,reply)


class Names(Command):
	name = 'w'
	rank = const.RANK_DISABLED
	file = __file__

	name_parser = argparse.ArgumentParser(prog='!w', add_help=False,
	epilog='''Key:\n* '@' - Admin\n* '%%' - Mod\n* '-' - Away\n* '!' - Busyn\* '#' - Banned''')
	name_parser.add_argument('nil', help=argparse.SUPPRESS)

	#Setup the doc string with the help text from the argument parser.
	__doc__ = """List status of users.\n%s""" % (name_parser.format_help())

	@classmethod
	def thread(cls, bot):
		statuses ={
			'admins' : [],
			'online' : [],
			'offline' : [],
			'away' : [],
			'idle' : [],
			'busy' : []
		}

		user, args = yield
		for sid in bot.xmpp.roster:
			i = utils.getjid(sid)
			name = utils.getnickname(i)
			if name == iMan.config.server.username:
				continue

			if not utils.isonline(cls.parent, sid):
				#statuses['offline'].append('(%s)' % name)
				continue

			jid_status = cls.parent.getJidStatus(sid)

			for who,(status,display) in jid_status.iteritems():
				if '@' not in unicode(who):
					continue
				if utils.isbanned(who):
						name = "#%s" % name
						continue

				if utils.isactive(cls.parent, who):
					if utils.isadmin(who):
						name = "@%s" % name
						#statuses['admins'].append(name)
					elif utils.ismod(who):
						name = "%"+"%s" % name
						#statuses['admins'].append(name)
					statuses['online'].append(name)
					break

				#Anyone not "available".
				elif utils.isaway(cls.parent, who):
					if status in ["away","xa"]:
						name = "-%s" % name
						statuses['idle'].append(name)
					elif status == "dnd":
						name = "!%s" % name
						statuses['busy'].append(name)
					break

		# Setup the header with a header for total number of users.
		reply = 'Users (%s):\n'
		total = 0
		for status, users in statuses.iteritems():
			if not users:
				continue
			reply += '%s (%s): %s\n' % (status, len(users), ' '.join(users))
			total += len(users)

		# Tack on the total number of users.
		reply = reply % total

		cls.parent.sendto(user, reply)
