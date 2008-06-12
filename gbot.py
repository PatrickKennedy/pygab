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

from __future__ import with_statement

import	os
import	sys
import	time
import	traceback
import	xmpp

import	bot
import	const

from	ini 	import	iMan
from	utils	import	*
from	gbot	import	*

# We're setting up
selfpath = sys.argv[0]
selffile = os.path.split(selfpath)[1]
MODULE = os.path.splitext(selffile)[0]
iMan.load('config', MODULE)

# Contains all the server information
server = iMan.config.server


def log(*args):
	"""Replacement for print, which doesn't deal with unicode well"""
	msg=u" ".join(map(unicode,args))
	# Replace unencodable charactors with ?
	print >>bot.logf, time.strftime("%Y-%m-%d %H:%M:%S"), msg.encode(sys.getdefaultencoding(),"replace")
	bot.logf.flush()
	print time.strftime("%H:%M:%S"), msg.encode(sys.getdefaultencoding(),"replace")

class ConferenceBot(bot.Bot):
	def __init__(self):

		#Start all the behind the scenes functions.
		bot.Bot.__init__(self, server.username, server.password, server.domain)

		# Load Module specific ini files.
		self.module = MODULE

		# Start timers.
		self.addTimer(20, iMan.saveall, None, type='seconds')

		#Plugin hashing dictionary
		self._pluginhash = {}
		self.pluginpaths = [self.module, '']

		self.load_plugins()

	def prep(self, secure=True):
		try:
			self.connect(
				(server.host, server.port),
				use_srv=False,
				secure=secure,
				resource=server.resource
			)
		except bot.ConnectError, serv:
			print "Unable to connect to server. %s:%s" % serv.message
			sys.exit(1)
		except bot.AuthError, serv:
			print "Unable to authorize on %s:%s - check login/password." % serv.message
			sys.exit(1)

	def reconnect(self):
		delay = 5
		debug('connection', 'Attempting to reconnect in %s seconds.' % delay)
		time.sleep(delay)
		try:
			self.client.reconnectAndReauth()
		except AttributeError:
			debug('connection', 'Failed to reconnect. Making new connection' /
								' in %s seconds.' % delay)
			time.sleep(delay)
			self.prep()

		self.setOnline()

	def load_plugins(self):
		confirmdir("errors")
		pluglog = file(os.path.join('.', 'errors', "PluginError-%s.log" % self.module), "a+")
		#Load all external plugins and warn the user about missing plugins.
		for i in iMan.config.system.plugins:
			try:
				plug_path = self.get_plugin_path(i)
				self.load_plugin(i, plug_path)
			except IOError, e:
				debug('plugins', 'The plugin "plugin_%s.py" could not be found.' % i)
				continue
			except:
				self.unload_plugin(plug_path)
				traceback.print_exc()
				print >>pluglog, "\n Plugin error log for: ", i
				traceback.print_exc(None, pluglog)
				debug('plugins', 'There was an error importing the plugin. A report has been logged.')
				continue
		pluglog.close()

	def get_plugin_path(self, name):
		for folder in self.pluginpaths:
			plug_path = os.path.abspath(os.path.join(
				'.', folder,
				'plugins','plugin_%s.py' % name
			))
			if os.path.exists(plug_path):
				return plug_path
		else:
			raise IOError

	def load_plugin(self, name, path_):
		with open(path_, "r") as f:
			a = f.read()
		# Skip plugins that haven't been updated.
		if self._pluginhash.get(name, 0) == hash(a):
			return False

		# Replicate __file__ in the plugin, since it isn't set by the
		# interpreter when it executes a string.
		# We're using __file__ to know what command classes to unload.
		plugin = {'__file__':path_}
		exec a in plugin
		# If the plugin has any initialization to be done, handle that here.
		handler = PluginInitializers.plugins.get(path_)
		if handler:
			handler(self)

		debug('core', "Loading Plugin (%s)" % name)
		self._pluginhash[name] = hash(a)
		return True

	def unload_plugin(self, path_):
		debug('core', "Unloading Plugin (%s)" % path_)
		initalizer = PluginInitializers.plugins.get(path_)
		if initalizer:
			initalizer(self).__exit__()

		for cmd in CommandMount.plugins.values():
			if cmd.file == path_:
				cmd(self).__exit__()

		for hook in HookMount.plugins.values():
			if hook.file == path_:
				hook(self).__exit__()

	def log(self,*args):
		log(*args)

	def hook(self, loc, *args, **kwargs):
		'''hook(str, loc, *args, **kwargs) -> bool

		Run all persistent hooks at 'loc' and return False if any non-persistent
		hooks return True.

		'''
		# Multiple plugins can register hooks, the first one to
		# return True causes all further processing of that hook
		# to be aborted.
		#print "Running hook. (Loc: %s)" % loc
		for hook in HookMount.get_plugin_list(loc=loc, persist=True):
			hook(self).run(*args, **kwargs)

		for hook in HookMount.get_plugin_list(loc=loc, persist=None):
			#print "Checking hook (%s) located at: %s" % (hook, hook.loc)
			if hook(self).run(*args, **kwargs):
				return False
		return True

	def command(self, user, msg):
		args = ''
		if " " in msg:
			cmd, args = msg.split(" ",1)
			cmd = cmd.lower()
		else:
			cmd = msg.strip().lower()
		#FIXME: This is a work around for shlex's poor unicode support.
		args = args.encode(sys.getdefaultencoding(),"replace")

		try:
			cmd_func = CommandMount.plugins.get(cmd)
			if not cmd_func:
				self.error(user, "Unknown command, try !help")
				return

			#assert isinstance(cmd, CommandMount

			if cmd_func.rank == const.RANK_USER:
				cmd_func(self).run(user, args)

			elif cmd_func.rank == const.RANK_MOD:
				if has_rank(user, const.RANK_MOD) or has_rank(user, const.RANK_ADMIN):
					cmd_func(self).run(user, args)
				else:
					self.error(user, "You must be a moderator to use that command.")

			elif cmd_func.rank == const.RANK_ADMIN:
				if has_rank(user, const.RANK_ADMIN):
					cmd_func(self).run(user, args)
				else:
					self.error(user, "You must be an admin to use that command.")

			else:
				self.error(user, "Unknown command, try !help")

		except CommandHelp, args:
			self.sys(user, func.__doc__)

		except CommandError, args:
			self.error(user, 'There was a problem with your command (%s) Sorry!' % cmd)

		except:
			print 'An error happened in the command: %s' % cmd
			traceback.print_exc()
			self.error(user, 'There was a problem with your command (%s) Sorry!' % cmd)

	def sendtoall(self, msg, butnot = []):
		'''Send msg to all online users exclusing anyone in butnot.'''
		for user in self.getRoster():
			# Skip any users in butnot
			if user in butnot:
				continue
			for resource,(status,display) in self.getJidStatus(user).items():
				# Ignore people who aren't online
				if status in [u"online", u"chat"]:
					self.msg(resource, msg)

		self.log(msg)

	def sendto(self, user, msg):
		'''Send msg to user via self.msg'''
		self.msg(user, msg)

	def sys(self, user, msg):
		self.sendto(user, '%s %s' % (iMan.config.system.sysprefix, msg))

	def systoall(self, msg, butnot=[], log = True):
		self.sendtoall('%s %s' % (iMan.config.system.sysprefix, msg), butnot, log = log)

	def error(self, user, msg):
		"Send an error message to a user"
		self.sendto(user, "ERROR: %s" % msg)

	def ev_msg(self, user, msg):
		user = getjid(user.getStripped())
		# Is this a command?
		if msg[:1] in iMan.config.system.commandprefix:
			self.command(user, msg[1:])
		elif user != getjid(server.username):
			if self.hook(const.LOC_EV_MSG, user, msg):
				# self.log("<%s> %s" % (getnickname(user), msg))
				self.sendtoall("<%s> %s" % (getnickname(user), msg),
								butnot=[unicode(user)]
				)

	def ev_iq(self, user, msg):
		# Process persistant hooks.
		if not self.hook(const.LOC_EV_IQ, user, msg):
			return

	def ev_unsubscribe(self, user, msg):
		if not self.hook(const.LOC_EV_UNSUBSCRIBE, user, msg):
			return

		user = user.getStripped()
		# User removed us from their list
		# So remove them from ours.
		log(user, "unsubscribing:", msg)
		self.removeUser(user)
		self.rejectUser(user)
		self.refreshRoster()

	def ev_unsubscribed(self, user, msg):
		"""User has forced us to remove them from our list."""
		if not self.hook(const.LOC_EV_UNSUBSCRIBED, user, msg):
			return

		user = user.getStripped()
		log(user, "unsubscribing:", msg)
		self.removeUser(user)
		# Remove us from their list
		self.rejectUser(user)
		self.refreshRoster()

	def ev_subscribe(self, user, msg):
		if not self.hook(const.LOC_EV_SUBSCRIBE, user, msg):
			return

		#FIXME: Currently getjid can only rebuild JID's with gmail.com domains,
		# so we need to reject not gmail.com users.
		if not user.get_domain() == server.domain:
			self.removeUser(user)
			return

		user = user.getStripped()
		# User added us to their list, so add them to ours
		log(user, "subscribing:", msg)
		self.addUser(user)
		self.acceptUser(user)
		self.refreshRoster()

	def ev_subscribed(self, user, msg):
		if not self.hook(const.LOC_EV_SUBSCRIBED, user, msg):
			return

	def ev_unavilable(self, user, status):
		# Process persistant hooks.
		if not self.hook(const.LOC_EV_UNAVILABLE, user, status):
			return

	def ev_online(self, user, status):
		# Process persistant hooks.
		if not self.hook(const.LOC_EV_ONLINE, user, status):
			return

	def ev_away(self, user, status):
		# Process persistant hooks.
		if not self.hook(const.LOC_EV_AWAY, user, status):
			return

	def ev_chat(self, user, status):
		# Process persistant hooks.
		if not self.hook(const.LOC_EV_CHAT, user, status):
			return

	def ev_dnd(self, user, status):
		# Process persistant hooks.
		if not self.hook(const.LOC_EV_DND, user, status):
			return

	def ev_xa(self, user, status):
		# Process persistant hooks.
		if not self.hook(const.LOC_EV_XA, user, status):
			return

if __name__ == '__main__':
	me = ConferenceBot()

	me.prep()
	me.setOnline()

	#Add any new users.
	#for i in me.getRoster():
	#	i = getjid(i)
	#	if i not in userlist.keys():
	#		adduser(getname(i))

	debug('core', "The bot is now online!\nRunning version: %s\nAt %s" % (
			get_svn_revision(), time.strftime("%Y-%m-%d %H:%M:%S")
		))
	me.run()
