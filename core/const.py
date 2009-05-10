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

# Custom Exceptions
class ConnectError(Exception): pass
class AuthError(Exception): pass
class CommandHelp(Exception): pass
class CommandError(Exception): pass

# Ranks
# Basic rank constants.
RANK_USER	= 'user'
RANK_MOD 	= 'mod'
RANK_ADMIN	= 'admin'
RANK_BANNED	= 'banned'
RANK_DISABLED = 'disabled'
RANK_HIDDEN = 'hidden'

# Timer Delay Types
SECONDS = 'sec'
MINUTES = 'min'
HOURS 	= 'hour'

# Hook Attributes
# Passed to indicate an attribute simply needs to be defined to be accepted.
ATTR_DEFINED = 'def'
# Requires a specific attribute to NOT be defined.
ATTR_UNDEFINED = 'undef'

PRIORITY_CRITICAL = 10
# Persistant Hooks should NEVER return True
PRIORITY_PERSISTANT = 5
PRIORITY_NORMAL = 0

# Hook Locations
# ev_msg passes the sender and the sent message as a string.
LOC_EV_MSG		= 'ev_msg'
LOC_EV_MSG_PRE	= 'ev_msg_pre'
LOC_EV_MSG_POST	= 'ev_msg_post'

# ev_iq passes the calling user and the iq stanza.
LOC_EV_IQ		= 'ev_iq'
LOC_EV_IQ_PRE	= 'ev_iq_pre'
LOC_EV_IQ_POST	= 'ev_iq_post'

# presence events pass the user and their status as a string.
LOC_EV_ONLINE		= 'ev_online'
LOC_EV_ONLINE_PRE	= 'ev_online_pre'
LOC_EV_ONLINE_POST	= 'ev_online_post'
LOC_EV_AWAY			= 'ev_away'
LOC_EV_AWAY_PRE		= 'ev_away_pre'
LOC_EV_AWAY_POST	= 'ev_away_post'
LOC_EV_CHAT			= 'ev_chat'
LOC_EV_CHAT_PRE		= 'ev_chat_pre'
LOC_EV_CHAT_POST	= 'ev_chat_post'
LOC_EV_DND			= 'ev_dnd'
LOC_EV_DND_PRE		= 'ev_dnd_pre'
LOC_EV_DND_POST		= 'ev_dnd_post'
LOC_EV_XA			= 'ev_xa'
LOC_EV_XA_PRE		= 'ev_xa_pre'
LOC_EV_XA_POST		= 'ev_xa_post'

# Subscription events pass the user and (I'm guessing) a blank string.
LOC_EV_UNAVAILABLE		= 'ev_unavailable'
LOC_EV_UNAVAILABLE_PRE	= 'ev_unavailable_pre'
LOC_EV_UNAVAILABLE_POST	= 'ev_unavailable_post'
LOC_EV_SUBSCRIBE		= 'ev_subscribe'
LOC_EV_SUBSCRIBE_PRE	= 'ev_subscribe_pre'
LOC_EV_SUBSCRIBE_POST	= 'ev_subscribe_post'
LOC_EV_SUBSCRIBED		= 'ev_subscribed'
LOC_EV_SUBSCRIBED_PRE	= 'ev_subscribed_pre'
LOC_EV_SUBSCRIBED_POST	= 'ev_subscribed_post'
LOC_EV_UNSUBSCRIBE		= 'ev_unsubscribe'
LOC_EV_UNSUBSCRIBE_PRE	= 'ev_unsubscribe_pre'
LOC_EV_UNSUBSCRIBE_POST	= 'ev_unsubscribe_post'
LOC_EV_UNSUBSCRIBED		= 'ev_unsubscribed'
LOC_EV_UNSUBSCRIBED_PRE	= 'ev_unsubscribed_pre'
LOC_EV_UNSUBSCRIBED_POST= 'ev_unsubscribed_post'
