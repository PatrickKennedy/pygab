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
		iMan.load('roster', utils.get_module())
		#self.parent.addTimer(5, self.test_timer, repeat=5, type='seconds')

	def test_timer(self):
		print "Eggs are yummy. %s" % time.clock()

	def __exit__(self, *args):
		mounts.PluginInitializers.remove(self.__class__)
		self.parent.removeTimer('test_timer')

class HookRosterOnline(mounts.HookMount):
	name = 'HookRosterOnline'
	loc = [const.LOC_EV_ONLINE]
	file = __file__
	priority = const.PRIORITY_PERSISTANT

	@mounts.HookMount.thread_base
	def thread(self, user, status):
		iMan.roster[utils.getname(user).lower()].lastseen = None

class HookRosterActivity(mounts.HookMount):
	name = 'HookRosterActivity'
	loc = [const.LOC_EV_MSG]
	file = __file__
	priority = const.PRIORITY_PERSISTANT

	@mounts.HookMount.thread_base
	def thread(self, user, status):
		iMan.roster[utils.getname(user).lower()].activity = list(time.localtime())

class HookRosterOffline(mounts.HookMount):
	name = 'HookRosterOffline'
	loc = [const.LOC_EV_UNAVAILABLE]
	file = __file__
	priority = const.PRIORITY_PERSISTANT

	@mounts.HookMount.thread_base
	def thread(self, user, status):
		iMan.roster[utils.getname(user).lower()].lastseen = list(time.localtime())
		iMan.roster[utils.getname(user).lower()].activity = None
		del iMan.roster[utils.getname(user).lower()].afk

class HookRosterAFK(mounts.HookMount):
	name = 'HookRosterAFK'
	loc = [const.LOC_EV_MSG]
	file = __file__
	priority = const.PRIORITY_PERSISTANT

	r = re.compile('(?:afk|brb)[:/,]?\s?(?P<reason>.*)', re.I)

	@mounts.HookMount.thread_base
	def thread(self, user, msg):
		if iMan.loaded('roster'):
			roster = iMan.roster[utils.getname(user).lower()]
			if roster.has_key('afk'):
				del roster.afk
				self.parent.sendto(user, "Welcome Back!")
			else:
				match = self.r.match(msg)
				if not match:
					return
				reason = match.group('reason')
				roster.afk = reason
				self.parent.sendto(user, 'Good Bye, %s! Come back soon!' %
								   utils.getname(user))

class LastSeen(mounts.CommandMount):
	name = 'lastseen'
	rank = const.RANK_USER
	file = __file__

	lastseen_parser = argparse.ArgumentParser(prog='!lastseen', add_help=False)
	lastseen_parser.add_argument('username', const=True, nargs='?',
		metavar='username', help='Name of the user you\'re looking up.')

	__doc__ = """Display the last time a user was on.\n%s""" % (lastseen_parser.format_help())

	def _now(self):
		now = time.time.localtime()[:6]
		return datetime.datetime(*now)

	def _s(self, i):
		return (i != 1 and 's' or '')

	def date_diff(self, then):
		diff = (datetime.datetime.now() - then)
		seconds = diff.seconds
		minutes = seconds / 60
		hours = minutes / 60
		days = diff.days

		if days < 1:
			if seconds < 5:
				time = 'a moment ago'
			elif seconds < 60:
				time = '%d second%s ago' % (seconds, self._s(seconds))
			elif minutes < 60:
				time = '%d minute%s ago' % (minutes, self._s(minutes))
			elif hours < 24:
				time = '%s hour%s ago' % (hours, self._s(hours))
		else:
			if hours:
				time = '%d day%s and %d hour%s ago' % (days, self._s(days),
													   hours, self._s(hours))
			else:
				time = 'exactly %d day%s ago' % (days, self._s(days))
		return time

	@mounts.CommandMount.thread_base
	def thread(self, user, args, whisper):
		try:
			args = self.lastseen_parser.parse_args(shlex.split(args))
		except:
			args = None

		if not args or not args.username:
			raise const.CommandHelp
		username = utils.getname(user)

		orig_name = args.username
		name = args.username.lower()
		roster = iMan.roster[name]

		reply = '%s, ' % username

		#The target is the calling user.
		if username.lower() == name:
			reply = "are you really that conceited? You're right here!"

		# We've never seen the target before.
		elif not roster.has_key('lastseen'):
			reply += "who is %s?" % (orig_name)

		# The target is online.
		elif roster.lastseen is None:
			activity = roster.activity
			if roster.has_key('afk'):
				activity = datetime.datetime(*activity[:6])
				reply += "%s went AFK %s" % (orig_name, self.date_diff(activity))
				if roster.afk:
					reply += " and is %s" % roster.afk

				reply += "."
			else:
				activity = iMan.roster[name].activity
				if not activity or activity == "None":
					reply += "%s hasn't spoken a word since he logged on." % orig_name
				else:
					activity = datetime.datetime(*activity[:6])
					reply += '%s spoke %s' % (orig_name, self.date_diff(activity))
			#reply = '%s, %s is currently online.' % (username, orig_name)

		# NoneTypes are read as strings, these will be read for people who went
		# offline after the bot went offline. They'll be added back in once they
		# are seen by the bot again.
		elif iMan.roster[name].lastseen == "None":
			reply += "I don't know when %s went offline. I was sleeping. " \
					"I'm sorry." % (orig_name)
			#self.sendtoall("I find my lack of %s disturbing." % name)

		# If the target is not online.
		else:
			then = datetime.datetime(*iMan.roster[name].lastseen[:6])
			reply += 'I saw %s %s' % (orig_name, self.date_diff(then))

		if whisper:
			self.parent.sendto(user, reply)
		else:
			self.parent.sendtoall(reply)

	def cmd_lastseen(self, user, args):
		if False:
			#self.sendtoall('The last time I saw %s was at %s' % \
			#	(name, formattime(iMan.roster.lastseen[name])))

			# Use the datetime module to get the difference in times.
			# time_diff is a timedelta.
			days = ''
			hours = ''
			minutes = ''
			seconds = '0 seconds'

			dt1=datetime.datetime(*time.gmtime()[:6])
			dt2=datetime.datetime(*iMan.roster.lastseen[name][:6])
			time_diff = dt1 - dt2
			times = str(time_diff)[-8:].strip().split(':')

			# Check days
			if time_diff.days:
				days = '%s day%s, ' % (
					time_diff.days,
					(time_diff.days != 1 and 's' or '')
				)

			# Check hours
			if int(times[0]):
				hours = '%s hour%s, ' % (
					times[0],
					(int(times[0]) != 1 and 's' or '')
				)

			# Check minutes
			if int(times[1]):
				minutes = '%s minute%s' % (
					times[1],
					(int(times[1]) != 1 and 's' or '')
				)

			# Check seconds
			if int(times[2]):
				seconds = ' and %s second%s' % (
					times[2],
					(int(times[2]) != 1 and 's' or '')
				)

			self.parent.sendtoall('I haven\'t seen %s in %s%s%s%s' % (
				name, days, hours,
				minutes, seconds
			))

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


	@mounts.CommandMount.thread_base
	def thread(self, user, args, whisper):
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
		for cmd in mounts.CommandMount.plugins.itervalues():
			# Skip commands if a user doesn't match the command's rank.
			#if cmd.rank == CommandMount.RANK_USER:

			if cmd.rank == const.RANK_MOD:
				if utils.ismod(user) or utils.isadmin(user):
					mod_cmd_list.append(cmd)

			elif cmd.rank == const.RANK_ADMIN:
				if utils.isadmin(user):
					admin_cmd_list.append(cmd)

			else:
				user_cmd_list.append(cmd)

		reply += " | User Cmds: "
		reply += ', '.join([cmd.name for cmd in user_cmd_list])
		if mod_cmd_list:
			reply += " | Mod Cmds: "
			reply += ', '.join([cmd.name for cmd in mod_cmd_list])
		if admin_cmd_list:
			reply += " | Admin Cmds: "
			reply += ', '.join([cmd.name for cmd in admin_cmd_list])

		self.parent.sendto(user,reply)


class Names():#CommandMount):
	name = 'w'
	rank = const.RANK_USER
	file = __file__

	name_parser = argparse.ArgumentParser(prog='!w', add_help=False,
	epilog='''Key:\n* '@' - Admin\n* '%%' - Mod\n* '-' - Away\n* '!' - Busyn\* '#' - Banned''')
	name_parser.add_argument('nil', help=argparse.SUPPRESS)

	#Setup the doc string with the help text from the argument parser.
	__doc__ = """List status of users.\n%s""" % (name_parser.format_help())

	@mounts.CommandMount.thread_base
	def thread(self, user, args, whisper):
		statuses ={
			'admins' : [],
			'online' : [],
			'offline' : [],
			'away' : [],
			'idle' : [],
			'busy' : []
		}

		for i in self.parent.getRoster():
			i = getjid(i)
			name = getnickname(i)
			if name == iMan.config.server.username:
				continue
			jidStatus = self.parent.getJidStatus(i).items()
			if jidStatus != []:
				for who,(status,display) in jidStatus:
					if '@' not in unicode(who):
						continue
					if has_rank(who, 'banned'):
							name = "#%s" % name
							continue

					if [(jid, msg) for (jid, (status, msg)) in jidStatus if status in ["online","chat"]]:
						if has_rank(who, 'admin'):
							name = "@%s" % name
							statuses['admins'].append(name)
						elif has_rank(who, 'mod'):
							name = "%"+"%s" % name
							statuses['admins'].append(name)
						else:
							statuses['online'].append(name)
						break

					#Anyone not "available".
					elif [(jid, msg) for (jid, (status, msg)) in jidStatus if status in [u"away",u"dnd",u"xa"]]:
						if status in [u"away",u"xa"]:
							name = "-%s" % name
							statuses['idle'].append(name)
						elif status == u"dnd":
							name = "!%s" % name
							statuses['busy'].append(name)
						break
			else:
				pass#statuses['offline'].append('(%s)' % name)

		# Setup the header with a header for total number of users.
		reply = 'Users: (%s)\n'
		total = 0
		for status, users in statuses.iteritems():
			if not users:
				continue
			reply += '%s: (%s)\n%s\n\n' % (status, len(users), ' '.join(users))
			total += len(users)

		# Tack on the total number of users.
		reply = reply % total

		self.parent.sendto(user, reply)
