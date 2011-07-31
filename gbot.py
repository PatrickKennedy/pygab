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

import sleekxmpp
import logging

from common import pyni, utils
from common.locations import Locations
from framework.bot import BotTemplate
from framework.plugin import PluginFramework
from framework.timers import TimerFramework

#logging.basicConfig(level=logging.NOTSET)

class Bot(BotTemplate):
	def __init__(self):
		self.plugins = PluginFramework(self)
		self.timers = TimerFramework()

		with pyni.Config(utils.get_module(), 'config') as ini:
			BotTemplate.__init__(
				self,
				"%s@%s/%s" % (ini.server.username, ini.server.domain, ini.server.resource),
				ini.server.password
			)
			self.plugins.load(*ini.system.plugins)

		self.xmpp.schedule('bot_process', 1, self.timers.process, repeat=True)

	def run(self):
		net_log.info("Connecting")
		with pyni.Config(utils.get_module(), 'config') as ini:
			self.xmpp.connect((ini.server.host, ini.server.port))
		self.xmpp.process(threaded=False)

	def _send_msg(self, msg):
		"""Takes a message stanza rather than a jid and message"""
		user = msg['to']
		if Locations.SendMsgPerUser.visit(user, msg):
			return

		for resource, presence in self.xmpp.roster[user.bare]['presence'].items():
			user.resource = resource
			# This should logically be moved to a hook.
			if Locations.SendMsgPerResource.visit(user, resource, msg) or \
				presence['show'] in ["available", "online", "chat"]:
					self.xmpp.send(msg)
		return

		for resource,(show,status) in self.getJidStatus(user).items():
			# Ignore people who aren't online
			# XXX: The message needs to be updated for each resource
			if Locations.SendMsgPerResource.visit(user, resource, msg) or \
				show in ["online", "chat"]:
				self.xmpp.send(msg)

	def sendtoall(self, text, butnot=[]):
		'''Send msg to all online users excluding anyone in butnot.'''
		chat_log.info('All <- %s' % text)
		message = self.xmpp.make_message(
			self.xmpp.boundjid,
			text,
			mfrom=self.xmpp.boundjid
		)

		if	Locations.SendToAll.visit(message) or \
			Locations.SendMsgPerMsg.visit(message):
				return

		text = message['body']
		for user in self.xmpp.roster:
			if user in butnot:
				continue
			message = self.xmpp.make_message(
				utils.getjid(user),
				text,
				mfrom=self.xmpp.boundjid
			)
			self._send_msg(message)

	def sendto(self, user, text):
		'''Send msg to user via self._send_msg'''
		chat_log.info('%s <- %s' % (utils.getnickname(user), text))
		message = self.xmpp.make_message(
			utils.getjid(user),
			text,
			mfrom=self.xmpp.boundjid
		)
		if	Locations.SendTo.visit(message) or \
			Locations.SendMsgPerMsg.visit(message):
				return

		self._send_msg(message)

	def sys(self, user, msg):
		with Config(utils.get_module(), 'config') as config:
			self.sendto(user, '%s %s' % (config.system.sysprefix, msg))

	def systoall(self, msg, butnot=[]):
		with Config(utils.get_module(), 'config') as config:
			self.sendtoall('%s %s' % (config.system.sysprefix, msg), butnot)

	def error(self, user, msg):
		"Send an error message to a user"
		self.sendto(user, "ERROR: %s" % msg)

	def ev_connected(self, event):
		with pyni.Config(utils.get_module(), 'config') as ini:
			self.xmpp.sendPresence(pstatus=ini.system.status)

	@Locations.EvMsg.include_location_wrappers()
	def ev_msg(self, event):
		chat_log.info("%s -> %s" % (event['from'].bare, event['body']))
		Locations.EvMsg.visit(self, event["from"], event)
		#self.xmpp.sendMessage(event["from"], event["body"])


def initalize_loggers():
	import os, sys
	#logging.config.fileConfig(os.path.join(module_path, 'logging.conf'))
	# Disable base logger logging
	#base_log = logging.getLogger('')
	#base_log.removeHandler(base_log.handlers[0])

	global root_log, net_log, chat_log
	with pyni.Config(utils.get_module(), 'config') as ini:
		time_format = ini.system.timeformat

	log_path = os.path.join('.', utils.get_module(), ini.system.logpath)
	if not os.path.exists(log_path):
		os.mkdir(log_path)

	root_log = logging.getLogger('pygab')
	root_log.setLevel(logging.INFO)

	handler = logging.StreamHandler(sys.stdout)
	handler.setFormatter(logging.Formatter(
		'%(levelname)s:%(name)s:%(asctime)s:%(message)s', time_format))
	root_log.addHandler(handler)

	#--- Connection Logger -----------------------------------------------------
	net_log = logging.getLogger('pygab.net')
	handler = logging.handlers.TimedRotatingFileHandler(
		os.path.join(log_path, 'connection.log'),
		'midnight', 1, 0,'utf-8')
	handler.setFormatter(logging.Formatter(
		'%(levelname)s %(asctime)s %(message)s', time_format))
	net_log.addHandler(handler)

	#--- Chat Logger -----------------------------------------------------------
	chat_log = logging.getLogger('pygab.chat')
	handler = logging.handlers.TimedRotatingFileHandler(
		os.path.join(log_path, 'history.log'),
		'midnight', 1, 0,'utf-8')
	handler.setFormatter(logging.Formatter(
		'%(asctime)s %(message)s', time_format))
	chat_log.addHandler(handler)

initalize_loggers()

if __name__ == '__main__':
	try:
		bot = Bot()
		bot.run()
	except:
		import traceback
		print(traceback.format_exc())
		raise
