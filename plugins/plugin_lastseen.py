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

from	common import argparse, const, mounts, utils
from	common.ini import iMan

class Init(mounts.PluginInitializers):
	name = __file__

	def initialize(self):
		iMan.load([utils.get_module(), 'roster'])

	def __exit__(self, *args):
		iMan.unload('roster')
		mounts.PluginInitializers.remove(self.__class__)


class HookRosterKongAFK(mounts.HookMount):
	name = 'HookRosterKongAFK'
	loc = [const.LOC_EV_MSG_PRE, const.LOC_EV_CHAT,
		   const.LOC_EV_ONLINE, const.LOC_EV_UNAVAILABLE]
	file = __file__
	priority = const.PRIORITY_PERSISTANT

	def thread(self, user, status):
		roster = iMan.roster[utils.getname(user).lower()]
		if 'afk' in roster and roster.afk[0] == "AWOL (a.k.a. set AFK by the chat)":
			del roster.afk


class HookRosterOnline(mounts.HookMount):
	name = 'HookRosterOnline'
	loc = [const.LOC_EV_ONLINE]
	file = __file__
	priority = const.PRIORITY_PERSISTANT

	def thread(self, user, status):
		if utils.getname(user) == 'McKain':
			def f():
				self.parent.sendto(user, 'Howdy!')
			self.parent.addTimer(1, f, 0, type='seconds')
		iMan.roster[utils.getname(user).lower()].last_login = None

class HookRosterAway(mounts.HookMount):
	name = 'HookRosterAway'
	loc = [const.LOC_EV_AWAY]
	file = __file__
	priority = const.PRIORITY_PERSISTANT

	def thread(self, user, status):
		if utils.getname(user).lower().startswith('guest_'):
			return
		roster = iMan.roster[utils.getname(user).lower()]
		if not 'afk' in roster:
			# Add an automated message we can check to see if the user was
			# automatically set away in other hooks.
			# Also account for the 15 minute delay by subtracting 900 seconds.
			roster.afk = ["AWOL (a.k.a. set AFK by the chat)", time.time()-900]

class HookRosterLastMessage(mounts.HookMount):
	name = 'HookRosterLastMessage'
	loc = [const.LOC_EV_MSG_POST]
	file = __file__
	priority = const.PRIORITY_NORMAL

	def thread(self, user, status):
		iMan.roster[utils.getname(user).lower()].last_message = time.time()

class HookRosterOffline(mounts.HookMount):
	name = 'HookRosterOffline'
	loc = [const.LOC_EV_UNAVAILABLE]
	file = __file__
	priority = const.PRIORITY_PERSISTANT

	def thread(self, user, status):
		roster = iMan.roster[utils.getname(user).lower()]
		roster.last_login = time.time()

class HookRosterAFK(mounts.HookMount):
	name = 'HookRosterAFK'
	loc = [const.LOC_EV_MSG]
	file = __file__
	priority = const.PRIORITY_PERSISTANT

	r = re.compile('(?:afk|brb)[:/,\.]?\s?(?P<reason>.*)', re.I)
	nolp = re.compile('lunatic pandora', re.I)
	webies = [
		'Welcome Back, %s!',
		'%s, I\'ve been... Expecting you.',
		'Webies, %s!',
		'Ah, %s, my loyal servant. Hello.',
		'QUIT FIDGITING WOR- Oh my, %s! You didn\'t hear that!',
		'Oh, I\'ve been workin\' on the Railroad! All the live long day! %s! Sing with me!',
		'%s! I LOVE YOU!'
	]
	byes = [
		'Good Bye, %s! Come back soon!',
		'We know why you\'re leaving us, %s, and we are sad.',
		'%s, you come again soon, y\'hear!',
		'%s, if you immediately know the candlelight is fire, the meal was cooked a long time ago.',
		'FREEEEEEEEEEDOOOOOM! Say it with me, %s! FREEEEEEEEDOOOOOM!',
		'They sent the last guy away in a small iron box! Please don\'t make the same mistake, %s!',
		'Tallioh, %s!',
	]

	def thread(self, user, msg):
		if iMan.loaded('roster'):
			roster = iMan.roster[utils.getname(user).lower()]
			match = self.r.match(msg)
			if msg.startswith('((') and msg.endswith('))'):
				return False
			if not match and 'afk' in roster:
				timestamp = datetime.datetime.fromtimestamp(roster.afk[1])
				self.parent.sendto(
					user,
					(random.choice(self.webies) + " You were gone for %s") % (
						utils.getname(user),
						utils.time_since(timestamp, '.')
					)
				)
				del roster.afk
			elif match:
				reason = match.group('reason')
				reason = self.nolp.sub('', reason)
				roster.afk = [reason, time.time()]
				self.parent.sendto(user, random.choice(self.byes) % utils.getname(user))

class CleanUp(mounts.CommandMount):
	name = 'cleanup'
	rank = const.RANK_ADMIN
	file = __file__

	def time_diff_days(self, then):
		if isinstance(then, list):
			then = datetime.datetime(*then[:6])
			diff = (datetime.datetime.now() - then)
			return diff.days

		return 0

	def thread(self, user, dry_run, whisper):
		iMan.load('roster')
		try:
			self.parent.sendto(user, 'Beginning Clean Up.')
			removed = 0
			roster = iMan.roster
			for username, user_dict in roster.items():
				if self.time_diff_days(user_dict.get('lastseen')) >= 14:
					removed += 1
					if not dry_run:
						del roster[username]

			self.parent.sendto(user, 'Clean up complete! Removed %s entries.' % removed)
		finally:
			iMan.unload('roster')

class LastSeen(mounts.CommandMount):
	name = 'lastseen'
	rank = const.RANK_USER
	file = __file__

	truncate_to = 16
	if iMan.load(utils.get_module(), 'plugins', 'plugin_lastseen'):
		if 'truncate_to' not in iMan.plugin_lastseen:
			iMan.plugin_lastseen._comments['truncate_to'] = \
				"Truncate passed names to x characters.\nWon't truncate if 0."
			iMan.plugin_lastseen.truncate_to = truncate_to
		else:
			truncate_to = iMan.plugin_lastseen.truncate_to
		iMan.unload('plugin_lastseen')

	lastseen_parser = argparse.ArgumentParser(prog='!lastseen', add_help=False)
	lastseen_parser.add_argument('username', const=True, nargs='?',
		metavar='username', help='Name of the user you\'re looking up.')

	__doc__ = """Display the last time a user was on.\n%s""" % (lastseen_parser.format_help())

	def thread(self, user, args, whisper):
		# Sterilize the name to prevent abuse.
		if self.truncate_to:
			if ' ' in args:
				args, _ = args.split(' ', 1)
			if len(args) > self.truncate_to:
				args = args[:self.truncate_to]
		elif False:
			try:
				args = self.lastseen_parser.parse_args(shlex.split(args))
			except:
				args = None

		if not args:
			raise const.CommandHelp
		username = utils.getname(user)

		orig_name = args
		name = args.lower()
		roster = iMan.roster[name]

		reply = '%s, ' % username

		#The target is the calling user.
		if username.lower() == name:
			reply += "are you really that conceited? You're right here!"

		# We've never seen the target before.
		elif not roster:
			reply += "who is %s?" % (orig_name)

		# The user is AFK. AFK status is persistent across statuses
		elif 'afk' in roster:
			timestamp = datetime.datetime.fromtimestamp(roster.afk[1])
			sentence = "%s%%s went AFK %s" % (orig_name, utils.time_since(timestamp))
			# If the user is online
			if roster.last_login is None:
				reply += sentence % ''
			else:
				reply += sentence % "(offline)"

			if roster.afk[0]:
				reply += " and is %s" % roster.afk[0]
			reply += "."

		# We see the user as online
		elif 'last_login' in roster and roster.last_login is None:
			if not roster.last_message:
				reply += "%s hasn't spoken a word since he logged on." % orig_name
			else:
				timestamp = datetime.datetime.fromtimestamp(roster.last_message)
				reply += '%s spoke %s' % (orig_name, utils.time_since(timestamp))

		# The user is offline
		else:
			then = datetime.datetime.fromtimestamp(roster.last_login)
			reply += 'I saw %s %s' % (orig_name, utils.time_since(then))

		if False and whisper:
			self.parent.sendto(user, reply)
		else:
			self.parent.sendtoall(reply)
