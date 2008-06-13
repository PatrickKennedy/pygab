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

# Ranks
RANK_USER	= 'user'
RANK_MOD 	= 'mod'
RANK_ADMIN	= 'admin'
RANK_BANNED	= 'banned'

# Hook Locations
# ev_msg passes the sender and the sent message as a string.
LOC_EV_MSG		= 'ev_msg'
# ev_iq passes the calling user and the iq stanza.
LOC_EV_IQ		= 'ev_iq'

# presence events pass the user and their status as a string.
LOC_EV_ONLINE	= 'ev_online'
LOC_EV_AWAY		= 'ev_away'
LOC_EV_CHAT		= 'ev_chat'
LOC_EV_DND		= 'ev_dnd'
LOC_EV_XA		= 'ev_xa'

# Subscription events pass the user and (I'm guessing) a blank string.
LOC_EV_UNAVAILABLE	= 'ev_unavailable'
LOC_EV_SUBSCRIBE	= 'ev_subscribe'
LOC_EV_SUBSCRIBED	= 'ev_subscribed'
LOC_EV_UNSUBSCRIBE	= 'ev_unsubscribe'
LOC_EV_UNSUBSCRIBED	= 'ev_unsubscribed'
