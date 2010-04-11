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

import logging
import	os
import	sys
import	time
import	traceback
import	xmpp

def log(*args):
	"""Replacement for print, which doesn't deal with unicode well"""
	global me
	msg = ' '.join(map(unicode,args))
	# Replace unencodable charactors with ?
	msg = '%s %s' % (time.strftime("%Y-%m-%d %H:%M:%S"),
					 msg.encode(sys.getdefaultencoding(), "replace"))
	print msg
	print >> me.logf, msg
	me.logf.flush()

from	common		import const, mounts, utils
from	common.ini 	import iMan
from	framework	import BotFramework, PluginFramework
from	gbot		import	*

iMan.load('config', utils.get_module())
# Contains all the server information
server = iMan.config.server

conn_log = logging.getLogger('pygab.net')
class ConferenceBot(BotFramework, PluginFramework):
	def __init__(self):
		#Start all the behind the scenes functions.
		BotFramework.__init__(self, server.username, server.password, server.domain)
		PluginFramework.__init__(self)

		# Load Module specific ini files.
		self.module = utils.get_module()

		# Start timers.
		self.addTimer(20, iMan.saveall, None, type='seconds')

		plugins_to_load = iMan.config.system.plugins
		if isinstance(plugins_to_load, basestring):
			plugins_to_load = plugins_to_load.split(' ')
		self.load_plugins(plugins_to_load)

	def prep(self, secure=True):
		try:
			self.connect(
				(server.host, server.port),
				use_srv=False,
				secure=secure,
				resource=server.resource
			)
		except const.ConnectError, serv:
			conn_log.fatal("Unable to connect to server. %s:%s" % serv.message)
			sys.exit(1)
		except const.AuthError, serv:
			conn_log.fatal("Unable to authorize on %s:%s - check login/password." % serv.message)
			sys.exit(1)

	def reconnect(self, tries=5):
		"""reconnect(tries=5) -> bool

		Attempt to reconnect to the server `tries` number of times.

		"""
		delay = 5
		conn_log = logging.getLogger('pygab.net')
		#utils.debug('connection', 'Attempting to reconnect in %s seconds.' % delay)
		conn_log.info('Attempting to reconnect in %s seconds.' % delay)
		time.sleep(delay)
		try:
			self.client.reconnectAndReauth()
			self.setOnline()
			return True
		except AttributeError:
			#utils.debug('connection', 'Failed to reconnect. Making new connection'
			#					' in %s seconds.' % delay)
			conn_log.info('Failed to reconnect. Making new connection in'
						   ' %s seconds.' % delay)
			time.sleep(delay)
			self.prep()
			if tries:
				return self.reconnect(tries-1)

		return False

	def log(self,*args):
		log(*args)

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

	def ev_msg(self, user, msg, raw_msg):
		user = utils.getjid(user.getStripped())
		# Is this a command?
		if msg[:1] in iMan.config.system.commandprefix:
			self.command(user, msg[1:])
		elif user != utils.getjid(server.username):
			if self.hook(const.LOC_EV_MSG, user, msg):
				# self.log("<%s> %s" % (getnickname(user), msg))
				self.sendtoall("<%s> %s" % (utils.getnickname(user), msg),
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

	#utils.debug('core', "The bot is now online!\nRunning version: %s\nAt %s" % (
	#		utils.get_svn_revision(), time.strftime("%Y-%m-%d %H:%M:%S")
	#	))
	logging.getLogger('pygab').info("The %s module is now online!" % utils.get_module())
	logging.getLogger('pygab').info("Running version: %s" % utils.get_svn_revision())
	me.run()
