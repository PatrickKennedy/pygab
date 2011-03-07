#!/usr/bin/env python3
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

class _MatchAll:

    def match(self, xml):
        return True

class BotTemplate:

	active_user = property(lambda self: self.last_stanza.get('from', None))
	last_stanza = {} # Placeholder that implements 'get'

	def __init__(self, jid, password):
		self.xmpp = sleekxmpp.ClientXMPP(jid, password)
		self.add_event_handlers()

	def add_event_handlers(self):
		xmpp = self.xmpp
		xmpp.register_handler(
			sleekxmpp.xmlstream.handler.Callback(
				"Match All",
				_MatchAll(),
				self.ev_match_all
			)
		)

		xmpp.add_event_handler("failed_auth", self.ev_failed_auth)
		xmpp.add_event_handler("session_start", self.ev_connected)
		xmpp.add_event_handler("disconnected", self.ev_disconnected)

		xmpp.add_event_handler("message", self.ev_msg)

		xmpp.add_event_handler("presence_error", self.ev_presence_error)
		xmpp.add_event_handler("presence_form", self.ev_presence_form)
		xmpp.add_event_handler("presence_probe", self.ev_presence_probe)

		xmpp.add_event_handler("presence_subscribe", self.ev_subscribe)
		xmpp.add_event_handler("presence_subscribed", self.ev_subscribed)
		xmpp.add_event_handler("presence_unsubscribe", self.ev_unsubscribe)
		xmpp.add_event_handler("presence_unsubscribed", self.ev_unsubscribed)

		xmpp.add_event_handler("got_online", self.ev_online)
		xmpp.add_event_handler("got_offline", self.ev_offline)
		xmpp.add_event_handler("changed_status", self._ev_available)

	def ev_match_all(self, stanza):
		self.last_stanza = stanza

	def ev_failed_auth(self, event):
		pass

	def ev_connected(self, event):
		pass

	def ev_disconnected(self, event):
		pass

	def ev_msg(self, event):
		pass

	def ev_presence_error(self, presence):
		pass

	def ev_presence_form(self, presence):
		pass

	def ev_presence_probe(self, presence):
		pass

	def ev_subscribe(self, presence):
		pass

	def ev_subscribed(self, presence):
		pass

	def ev_unsubscribe(self, presence):
		pass

	def ev_unsubscribed(self, presence):
		pass

	def ev_online(self, presence):
		pass

	def ev_offline(self, presence):
		pass

	def _ev_available(self, presence):
		if presence['show'] not in presence.showtypes:
			self.ev_available(presence)
			return

		getattr(self, "ev_%s" % presence['show'])(presence)

	def ev_available(self, presence):
		pass

	def ev_unavailable(self, presenece):
		pass

	def ev_dnd(self, presenece):
		pass

	def ev_chat(self, presenece):
		pass

	def ev_xa(self, presenece):
		pass

	def ev_away(self, presenece):
		pass
