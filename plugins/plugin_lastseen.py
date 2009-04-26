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
		iMan.load('roster', utils.get_module())

	def __exit__(self, *args):
		mounts.PluginInitializers.remove(self.__class__)

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
		iMan.roster[utils.getname(user).lower()].last_login = time.time()
		iMan.roster[utils.getname(user).lower()].last_message = None
		del iMan.roster[utils.getname(user).lower()].afk

class HookRosterAFK(mounts.HookMount):
	name = 'HookRosterAFK'
	loc = [const.LOC_EV_MSG]
	file = __file__
	priority = const.PRIORITY_PERSISTANT

	r = re.compile('(?:afk|brb)[:/,\.]?\s?(?P<reason>.*)', re.I)
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
		'They sent the last guy away in a small iron box! Please don\'t make the same mistake, %s!'
	]

	def thread(self, user, msg):
		if iMan.loaded('roster'):
			roster = iMan.roster[utils.getname(user).lower()]
			match = self.r.match(msg)
			if msg.startswith('|') and msg.endswith('|'):
				return False
			if not match and roster.has_key('afk'):
				del roster.afk
				last_message = datetime.datetime.fromtimestamp(roster.last_message)
				self.parent.sendto(
					user, (random.choice(self.webies) + " You were gone for %s") % (
						utils.getname(user),
						utils.time_since(last_message, '.')
					)
				)
			elif match:
				reason = match.group('reason')
				roster.afk = reason
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

	def thread(self, user, args, whisper):
		if iMan.loaded('roster'):
			self.parent.sendto(user, 'Beginning Clean Up.')
			removed = 0
			roster = iMan.roster
			for username, user_dict in roster.items():
				if self.time_diff_days(user_dict.get('lastseen')) >= 14:
					removed += 1
					del roster[username]

			self.parent.sendto(user, 'Clean up complete! Removed %s entries.' % removed)
		else:
			self.parent.sendto(user, 'The roster is not loaded. I can\'t do anything')

class LastSeen(mounts.CommandMount):
	name = 'lastseen'
	rank = const.RANK_USER
	file = __file__

	lastseen_parser = argparse.ArgumentParser(prog='!lastseen', add_help=False)
	lastseen_parser.add_argument('username', const=True, nargs='?',
		metavar='username', help='Name of the user you\'re looking up.')

	__doc__ = """Display the last time a user was on.\n%s""" % (lastseen_parser.format_help())

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
		elif not roster.has_key('last_login'):
			reply += "who is %s?" % (orig_name)

		# The target is online.
		elif roster.last_login is None:
			try:
				last_message = datetime.datetime.fromtimestamp(roster.last_message)
			except TypeError:
				last_message = None

			if roster.has_key('afk'):
				reply += "%s went AFK %s" % (orig_name, utils.time_since(last_message))
				if roster.afk:
					reply += " and is %s" % roster.afk

				reply += "."
			else:
				if not last_message:
					reply += "%s hasn't spoken a word since he logged on." % orig_name
				else:
					reply += '%s spoke %s' % (orig_name, utils.time_since(last_message))
			#reply = '%s, %s is currently online.' % (username, orig_name)

		# NoneTypes are read as strings, these will be read for people who went
		# offline after the bot went offline. They'll be added back in once they
		# are seen by the bot again.
		elif iMan.roster[name].last_login == "None":
			reply += "I don't know when %s went offline. I was sleeping. " \
					"I'm sorry." % (orig_name)
			#self.sendtoall("I find my lack of %s disturbing." % name)

		# If the target is not online.
		else:
			then = datetime.datetime.fromtimestamp(iMan.roster[name].last_login)
			reply += 'I saw %s %s' % (orig_name, utils.time_since(then))

		if whisper:
			self.parent.sendto(user, reply)
		else:
			self.parent.sendtoall(reply)
