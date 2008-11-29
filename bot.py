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

import 	xmpp
import 	traceback
import 	os
import	sys
import 	time

# Add import paths
# This lets modules access common files.
#sys.path.append(os.path.abspath(os.path.join('.', 'common')))

from 	common.ini			import	iMan
from 	xml.parsers.expat	import	ExpatError

# This file deals with all the XMPP side of things
# It creates a "Bot" object which deals with taking commands and turning
# them into xmpp stanzas and sending them, as well as providing functions
# to override when events occur.

# You are expected to override functions beginning with "ev_"

# The "process" function is also available to be overridden.
# It is called directly after the jabber client's process function.

def _promote_jid(jid):
	"""_promote_jid(str jid) -> xmpp.protocol.JID

	Takes a string/unicode string and returns a JID object
	Returns the argument if it is already a JID

	"""
	if isinstance(jid,xmpp.protocol.JID):
		return jid
	return xmpp.protocol.JID(jid=jid)

# Custom Exceptions
class ConnectError(Exception): pass
class AuthError(Exception): pass

class Bot(object):
	def __init__(self, username, password, domain="gmail.com"):

		# Add import paths
		sys.path.append(os.path.abspath(os.path.join('.', 'common')))

		self.jid = xmpp.protocol.JID("%s@%s" % (username,domain))
		self.password = password
		self.timers = {}

# Things to do
	def connect(self, server=(), proxy={}, use_srv=False, secure=None, resource=''):
		"""connect(tuple server, dict proxy, bool use_srv, str resource)

		Connect to the server using the given arguments.
		server	: (host, port) tuple. May be blank to use defaults.
		proxy	: {host, port, user, password} dictionary, blank = no proxy.
		use_srv	: Attempts resolve the DNS of the given host.
		secure	: None attempts to use TLS/SSL if possible.
				: 1 Attempts to force use.
				: 0 Disables it altogther. (Use this if your server doesn't support it.)
		resorce	: The jabber resource for the bot.

		"""
		#traceback.print_exc()

		self.client = xmpp.Client(self.jid.getDomain(), debug=[])

		if server:
			conres = self.client.connect(server, proxy, use_srv=use_srv, secure=secure)
		else:
			conres = self.client.connect()
		if not conres:
			raise ConnectError(server)
		if conres != 'tls':
			print "Warning: Unable to estabilish secure connection - TLS failed!"

		#self.client.disconnect_handlers = []
		self.client.RegisterHandler('message',self._msgcb)
		self.client.RegisterHandler('iq',self._iqcb)
		self.client.RegisterHandler('presence',self._presencecb)

		authres = self.client.auth(self.jid.getNode(), self.password, resource)
		if not authres:
			raise AuthError(server)
		if authres != 'sasl':
			print "Warning: Unable to perform SASL auth os %s:%s. Old authentication method used!" % server

		self.client.sendInitPresence()

	def run(self):
		"""run() -> None

		Start processing commands untill stop() is called.

		"""
		self.running = True
		last_ping = last_activity = last_break = time.time()

		while self.running:
			try:
				#Montior day changes and changes in log location.
				log_path = os.path.join(
					'.', iMan.config.system.logpath or 'logs/kong',
					self.module
				)
				if not os.path.isdir(log_path):
					os.mkdir(log_path)
					print "ALERT: The dir doesn't exist, making (%s)" % log_path
				self.logf = file(os.path.join(log_path,
					time.strftime(iMan.config.system.logformat) + '.log'
				), "a+")

				# Send some kind of dummy message every few minutes to
				# tell Google we're still here.
				if time.time() - last_ping > 120: # every 2 minutes
					# Say we're online.
					last_ping = time.time()
					self.setOnline(iMan.config.system.status)

				#Run through the timer list and run any events
				#that haven't been run in their defined interval.
				self.processTimers()

				#print self.client.Process(1)
				self.client.Process(0.25)
				self.process()
			except KeyboardInterrupt, e:
				self.stop()
				sys.exit(0)
				break
			except AttributeError, e:
				traceback.print_exc()
				try:
					self.stop()
					self.reconnect()
					self.run()
				except:
					traceback.print_exc()
			except IOError, e:
				if e == 'Disconnected from server.':
					self.stop()
					self.reconnect()
					self.run()
				else:
					traceback.print_exc()
			except ExpatError, e:
				continue
			except:
				traceback.print_exc()
				continue

	def processTimers(self):
		"""processTimers() -> None

		Process any timers that have been set.
		Timers are deleted as they run out.
		This function can be replaced if needed.

		"""
		old_timers = []
		for event in self.timers:
			t = self.timers[event]
			if time.time() - t['last_run'] > t['delay']:# and t['repeat'] != 0:
				t['last_run'] = time.time()
				event(*t['args'])
				# Delete any finished timers.
				if t['repeat'] == 0:
					old_timers.append(event)
				# Deincriment time repeats.
				elif t['repeat'] > 0:
					t['repeat'] -= 1

		for event in old_timers:
			del self.timers[event]

	def process(self):
		"""process() -> None

		Process any custom features.

		"""
		pass

	def reconnect(self, tries=5):
		"""reconnect(tries=5) -> None

		Allow each module to define reconnect sequences.
		By default, the reconnect function handles all retry attempts.

		"""
		pass

	def disconnect(self):
		"""disconnect() -> None

		Disconnect and stop the bot

		"""
		self.client.disconnect()
		self.stop()

	def stop(self):
		"""stop() -> None

		Stop the bot's processing

		"""
		self.running = False
		self.logf.close()

	def addTimer(self, delay, event, repeat=-1, type="minutes",
				 run_now=False, args=[]):
		"""addTimer(int delay, callable event, repeat=-1,
					type='minutes', run_now=False args=[]) -> None

		Add an event to run at a set number of minutes.
		'args' are any extra arguments to be passed to the event.

		"""

		if type.lower() == "hours":
			delay = delay * 60 * 60
		elif type.lower() == "minutes":
			delay = delay * 60
		self.timers[event] = {
				'delay'		:	delay,
				'last_run'	:	run_now and 1 or time.time(),
				'repeat'	:	repeat,
				'args'		:	args
			}

	def removeTimer(self, timer_name):
		"""removeTimer(str timer_name) -> None

		Delete an event's timer instance.

		"""
		try:
			for timer in self.timers:
				if timer.__name__ in timer_name:
					del self.timers[timer]
		except:
			pass

# Messages to send
	def msg(self, jid, message):
		"""msg(JID jid, str message) -> None

		Send a message to the specified jid

		"""
		last_activity = time.time()
		self.client.send(xmpp.protocol.Message(jid, message))

# Roster management commands
	def addUser(self, jid):
		"""addUser(JID jid) -> None

		Asks a user to join your roster

		"""

		self.client.send(xmpp.protocol.Presence(
					to=jid, typ='subscribe'))
		self.refreshRoster()

	def removeUser(self, jid):
		"""removeUser(JID jid) -> None

		Removes a user from your roster

		"""
		self.client.send(xmpp.protocol.Presence(
					to=jid, typ='unsubscribe'))
		self.refreshRoster()

	def acceptUser(self,jid):
		"Allow a user to add you to their roster"
		self.client.send(xmpp.protocol.Presence(
					to=jid, typ='subscribed'))
		self.refreshRoster()

	def rejectUser(self,jid):
		"Remove yourself from a remote users roster/disallow adding"
		self.client.send(xmpp.protocol.Presence(
					to=jid, typ='unsubscribed'))
		self.refreshRoster()

	def DisconnectHandler(self):
		pass

	def _getSingleJidStatus(self, roster, jid):
		"Internal: Figures out the status for a fully qualifed jid"
		# Subscribing
		jid=unicode(jid)
		if roster.getAsk(jid) == "subscribe":
			return u"subscribe",u""
		show = {
			"away" : u"away",
			None : u"online",
			"xa" : u"xa",
			"dnd" : u"dnd",
			"chat" : u"chat",
		}[roster.getShow(jid)]
		status = roster.getStatus(jid)
		if status is None:
			status = u""
		return show,status

	def getJidStatus(self,jid):
		"""getJidStatus(jid) -> dict
		Returns a dict of all this users resources to a tuple of their status
		(subscribe/away/online/xa/dnd/chat) and message
		"""
		roster=self.client.getRoster()
		jid=_promote_jid(jid)
		if jid.getResource() == '':
			resources = roster.getResources(unicode(jid))
		else:
			resources = [jid.getResource()]
		res = {}
		for resource in resources:
			fjid = xmpp.protocol.JID(
				node=jid.getNode(),
				domain=jid.getDomain(),
				resource=resource)
			res[fjid] = self._getSingleJidStatus(roster,fjid)
		return res

	def getRoster(self):
		"Return all the users in the roster"
		roster = self.client.getRoster()
		return roster.getItems()

	def refreshRoster(self):
		"Request a new roster from the server."
		roster = self.client.getRoster()
		roster.Request(True)

# Change bots status
	def setOnline(self, msg=None, to=None):
		"Set the bot 'Online'"
		self.client.send(xmpp.protocol.Presence(to=to,status=msg))

	def setUnavailable(self, msg=None, to=None):
		"Set the bot 'Offline'"
		self.client.send(xmpp.protocol.Presence(
					to=to,status=msg,show='unavailable'))

	def setAway(self, msg=None, to=None):
		"Set the bot 'Away'"
		self.client.send(xmpp.protocol.Presence(
					to=to,status=msg,show='away'))

	def setDND(self, msg=None, to=None):
		"Set the bot 'Do Not Disturb'"
		self.client.send(xmpp.protocol.Presence(
					to=to,status=msg,show='dnd'))

	def setXA(self, msg=None, to=None):
		"Set the bot 'eXtended Away'"
		self.client.send(xmpp.protocol.Presence(
					to=to,status=msg,show='xa'))

# Message related events
	def ev_msg(self, user, text, raw_msg):
		"Override me: Called with new messages"
		pass

# Presence related events
	def ev_subscribe(self, user, msg):
		"User requests to add you to their roster"
		pass

	def ev_subscribed(self, user, msg):
		"User has been added to the bots roster"
		pass

	def ev_unavailable(self, user, msg):
		"User went offline"
		pass

	def ev_unsubscribe(self, user, msg):
		"User requestes removal from their roster"
		pass

	def ev_unsubscribed(self, user, msg):
		"User has been removed from the bots roster"
		pass

	def ev_online(self, user, msg):
		"User is now online"
		pass

	def ev_away(self, user, msg):
		"User is away"
		pass

	def ev_chat(self, user, msg):
		"User is interested in chatting"
		pass

	def ev_dnd(self, user, msg):
		"User is Do Not Disturb"
		pass

	def ev_xa(self, user, msg):
		"User is eXtended Away"
		pass

# Queries
	def ev_iq(self, user, iq):
		"Information Query"
		pass

# Internal XMPP callbacks
	def _msgcb(self, conn, mess):
		"Internal: Recieve a message from the server"
		#print mess
		if mess.getError() != None:
			if mess.getError() != "recipient-unavailable":
				print """Message Error:
	Message: %s
	Error: %s""" % (mess.getBody(), mess.getError())
			return

		if mess.getType() == "chat":
			pass#print mess

		text = mess.getBody()
		user = mess.getFrom()

		#Prevents "NoneTypes" from causing errors.
		if text is not None:
			self.ev_msg(user, text, raw_msg=mess)

	def _presencecb(self, conn, pres):
		presTypes1={
			"subscribe"		: self.ev_subscribe,
			"subscribed"	: self.ev_subscribed,
		}
		presTypes2={
			"unsubscribe"	: self.ev_unsubscribe,
			"unsubscribed"	: self.ev_unsubscribed,
			"unavailable" 	: self.ev_unavailable,
		}
		presShows={
			"away" 	: self.ev_away,
			"chat"	: self.ev_chat,
			"dnd"	: self.ev_dnd,
			"xa"	: self.ev_xa,
		}

		user = pres.getFrom()
		if pres.getType() == "error":
			print pres

		msg = pres.getStatus()
		if msg is None:
			msg = ""

		flag = 0

		# Deal with subscription etc
		if pres.getType() in presTypes1:
			presTypes1[pres.getType()](user, msg)
			flag = 1

		# Deal with away/chat/dnd/xa
		if pres.getShow() in presShows:
			presShows[pres.getShow()](user, msg)
			flag = 1

		# they're "just" online
		if pres.getType() is None and pres.getShow() is None:
			self.ev_online(user,msg)
			flag = 1

		# Deal with unsubscription etc
		if pres.getType() in presTypes2:
			presTypes2[pres.getType()](user, msg)
			flag = 1

		if flag == 0:
			print "Unknown Presence:", user, "\nType:",`pres.getType()`, " Show:",`pres.getShow()`, "\nStatus:",`pres.getStatus()`, "\nMessage:",msg

	def _iqcb(self, conn, iq):
		#print iq
		self.ev_iq(iq.getFrom(), iq)

if __name__ == '__main__':
	print "bot.py is not meant to be run on it's own. Please run a provided module (eg. gbot.py)"
	sys.exit()
