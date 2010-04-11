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

class EightBall(mounts.CommandMount):
	name = '8ball'
	rank = const.RANK_USER
	file = __file__
	__doc__ = "Ask me a Yes, No, or Maybe So question and I'll give you the answer."

	messages = [
		'Signs point to yes.', 'Yes.', 'Reply hazy, try again.',
		'Without a doubt.', 'My sources say no.', 'As I see it, yes.',
		'You may rely on it.', 'Concentrate and ask again.',
		'Outlook not so good.', 'It is decidedly so.',
		'Better not tell you now.', 'Very doubtful.', 'Yes - definitely.',
		'It is certain.', 'Cannot predict now.', 'Most likely.',
		'Ask again later.', 'My reply is no.', 'Outlook good.',
		'Don\'t count on it.',
	]

	alt_messages = [
		'Yes, in due time.', 'My sources say no.', 'Definitely not.', 'Yes.',
		'You will have to wait.', 'I have my doubts.', 'Outlook so so.',
		'Looks good to me!', 'Who knows?', 'Looking good!', 'Probably.',
		'Are you kidding?', 'Go for it!', 'Don\'t bet on it.', 'Forget about it.',
	]

	combined_messages = messages + alt_messages

	def thread(self, user, args, whisper):
		if not args.endswith('?'):
			raise const.CommandHelp

		if self.parent.was_whispered:
			self.parent.sendto(user, random.choice(self.combined_messages))
		else:
			self.parent.sendtoall(random.choice(self.combined_messages))
