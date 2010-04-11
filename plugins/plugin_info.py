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
import	re
import	shlex
import	time

from	common			import argparse, const, mounts, utils
from	common.ini		import iMan
#from	common.utils	import *

#module = get_module()
#exec(get_import(mod=module, from_=['utils']))
#try:
#	exec(get_import(mod=module, from_=['mounts'],
#		import_=['PluginInitializers', 'HookMount', 'CommandMount']))
#except ImportError, e:
#	print e

class Init(mounts.PluginInitializers):
	name = __file__

	def initialize(self):
		iMan.load([utils.get_module(), 'roster'])
		#self.parent.addTimer(5, self.test_timer, repeat=5, type='seconds')

	def test_timer(self):
		print "Eggs are yummy. %s" % time.clock()

	def __exit__(self, *args):
		mounts.PluginInitializers.remove(self.__class__)
		self.parent.removeTimer('test_timer')

class Help(mounts.CommandMount):
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



	def thread(self, user, args):
		args = self.help_parser.parse_args(shlex.split(args))
		if args.cmd:
			if args.cmd in mounts.CommandMount.plugins.keys():
				self.parent.sendto(user, mounts.CommandMount.plugins[args.cmd].__doc__)
			else:
				self.parent.error(user, "I don't know that command (%s)."
					" Please check your spelling." % args.cmd)
			return

		reply = "Cmd Prefix: %s" % (iMan.config.system.commandprefix)

		user_cmd_list = []
		mod_cmd_list = []
		admin_cmd_list = []
		disabled_cmd_list = []
		for cmd in mounts.CommandMount.plugins.itervalues():
			# Skip commands if a user doesn't match the command's rank.
			#if cmd.rank == CommandMount.RANK_USER:

			if cmd.rank == const.RANK_USER:
				user_cmd_list.append(cmd.name)
			elif cmd.rank == const.RANK_MOD:
				mod_cmd_list.append(cmd.name)
			elif cmd.rank == const.RANK_ADMIN:
				admin_cmd_list.append(cmd.name)
			elif cmd.rank == const.RANK_DISABLED:
				disabled_cmd_list.append(cmd.name)

		reply += " | User Cmds: "
		reply += ', '.join(user_cmd_list)
		if mod_cmd_list and (utils.ismod(user) or utils.isadmin(user)):
			reply += " | Mod Cmds: "
			reply += ', '.join(mod_cmd_list)
		if admin_cmd_list and utils.isadmin(user):
			reply += " | Admin Cmds: "
			reply += ', '.join(admin_cmd_list)
		if disabled_cmd_list and (utils.ismod(user) or utils.isadmin(user)):
			reply += " | Disabled Cmds: "
			reply += ', '.join(disabled_cmd_list)

		self.parent.sendto(user,reply)


class Names(mounts.CommandMount):
	name = 'w'
	rank = const.RANK_USER
	file = __file__

	name_parser = argparse.ArgumentParser(prog='!w', add_help=False,
	epilog='''Key:\n* '@' - Admin\n* '%%' - Mod\n* '-' - Away\n* '!' - Busyn\* '#' - Banned''')
	name_parser.add_argument('nil', help=argparse.SUPPRESS)

	#Setup the doc string with the help text from the argument parser.
	__doc__ = """List status of users.\n%s""" % (name_parser.format_help())


	def thread(self, user, args):
		statuses ={
			'admins' : [],
			'online' : [],
			'offline' : [],
			'away' : [],
			'idle' : [],
			'busy' : []
		}

		for sid in self.parent.getRoster():
			i = utils.getjid(sid)
			name = utils.getnickname(i)
			if name == iMan.config.server.username:
				continue

			if not utils.isonline(self.parent, sid):
				#statuses['offline'].append('(%s)' % name)
				continue

			jid_status = self.parent.getJidStatus(sid)

			for who,(status,display) in jid_status.iteritems():
				if '@' not in unicode(who):
					continue
				if utils.isbanned(who):
						name = "#%s" % name
						continue

				if utils.isactive(self.parent, who):
					if utils.isadmin(who):
						name = "@%s" % name
						#statuses['admins'].append(name)
					elif utils.ismod(who):
						name = "%"+"%s" % name
						#statuses['admins'].append(name)
					statuses['online'].append(name)
					break

				#Anyone not "available".
				elif utils.isaway(self.parent, who):
					if status in [u"away",u"xa"]:
						name = "-%s" % name
						statuses['idle'].append(name)
					elif status == u"dnd":
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

		self.parent.sendto(user, reply)
