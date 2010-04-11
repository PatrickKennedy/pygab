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
import os
import sys
import time
import traceback

import xmpp
import user

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

from common		import const, mounts, utils
from common.ini 	import iMan
from framework.bot	import BotFramework
from framework.plugin import attach_hooks, attach_post_hook, PluginFramework
from gbot		import	*


iMan.load(utils.get_module(), 'config')
# Contains all the server information
server = iMan.config.server

conn_log = logging.getLogger('pygab.net')


class ConferenceBot(BotFramework, PluginFramework):
	def __init__(self):
		logging.info('Running %s' % utils.get_module())

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

	def _send_msg(self, msg):
		"""Takes a message stanza rather than a jid and message"""
		if self.hook(const.LOC_SEND_MSG_PER_USER, msg.to_user, msg):
			return
		for resource,(show,status) in self.getJidStatus(msg.to_user).items():
			# Ignore people who aren't online
			if self.hook(const.LOC_SEND_MSG_PER_RESOURCE, resource, msg) or \
				show in [u"online", u"chat"]:
				self.client.send(msg)

	def sendtoall(self, text, butnot=[]):
		'''Send msg to all online users excluding anyone in butnot.'''
		logging.getLogger('pygab.chat').info('All <- %s' % text)
		if self.hook(const.LOC_SEND_MSG_PER_MSG, text):
			return

		for user in self.getRoster():
			if user in butnot:
				continue
			message = self._build_msg(utils.getjid(user), text)
			self._send_msg(message)

	def sendto(self, user, text):
		'''Send msg to user via self._send_msg'''
		logging.getLogger('pygab.chat').info('%s <- %s' % (utils.getnickname(user), text))
		message = self._build_msg(utils.getjid(user), text)
		if self.hook(const.LOC_SEND_MSG_PER_MSG, message):
			return

		self._send_msg(message)

	def sys(self, user, msg):
		self.sendto(user, '%s %s' % (iMan.config.system.sysprefix, msg))

	def systoall(self, msg, butnot=[]):
		self.sendtoall('%s %s' % (iMan.config.system.sysprefix, msg), butnot)

	def error(self, user, msg):
		"Send an error message to a user"
		self.sendto(user, "ERROR: %s" % msg)

	@attach_hooks()
	def ev_msg(self, msg):
		user = utils.getjid(msg.from_user.getStripped())
		if user != utils.getjid(server.username):
			if self.hook(const.LOC_EV_MSG, msg):
				# TODO: Log all incoming to the console and
				# all outgoing to a file.
				logging.getLogger('pygab.chat').info('%s -> %s' % (
					utils.getnickname(msg.from_user), msg.text
				))
				return
			# self.log("<%s> %s" % (getnickname(user), msg))
			text = '<%s> %s' % (utils.getnickname(msg.from_user), msg.text)
			self.sendtoall(text, butnot=[unicode(user)])

	@attach_hooks()
	def ev_iq(self, iq):
		# Process persistent hooks.
		if self.hook(const.LOC_EV_IQ, iq):
			return

	@attach_hooks()
	def ev_unsubscribe(self, pres):
		"""User has forced us to remove them from our list."""
		if self.hook(const.LOC_EV_UNSUBSCRIBE, pres):
			return

		user = user.getStripped()
		# User removed us from their list
		# So remove them from ours.
		log(user, "unsubscribing:", pres.getStatus())
		self.removeUser(user)
		# Remove us from their list
		self.rejectUser(user)
		self.refreshRoster()

	@attach_hooks()
	def ev_subscribe(self, pres):
		if self.hook(const.LOC_EV_SUBSCRIBE, pres):
			return

		#FIXME: Currently getjid can only rebuild JID's with gmail.com domains,
		# so we need to reject not gmail.com users.
		if not user.get_domain() == server.domain:
			self.removeUser(user)
			return

		user = user.getStripped()
		# User added us to their list, so add them to ours
		log(user, "subscribing:", pres.getStatus())
		self.addUser(user)
		self.acceptUser(user)
		self.refreshRoster()

	@attach_hooks()
	def ev_subscribed(self, pres):
		if self.hook(const.LOC_EV_SUBSCRIBED, pres):
			return

	@attach_hooks()
	def ev_unavilable(self, pres):
		# Process persistant hooks.
		if self.hook(const.LOC_EV_UNAVILABLE, pres):
			return

	@attach_hooks()
	def ev_online(self, pres):
		# Process persistant hooks.
		if self.hook(const.LOC_EV_ONLINE, pres):
			return

	@attach_hooks()
	def ev_away(self, pres):
		# Process persistant hooks.
		if self.hook(const.LOC_EV_AWAY, pres):
			return

	@attach_hooks()
	def ev_chat(self, pres):
		# Process persistant hooks.
		if self.hook(const.LOC_EV_CHAT, pres):
			return

	@attach_hooks()
	def ev_dnd(self, pres):
		# Process persistant hooks.
		if self.hook(const.LOC_EV_DND, pres):
			return

	@attach_hooks()
	def ev_xa(self, pres):
		# Process persistant hooks.
		if self.hook(const.LOC_EV_XA, pres):
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
