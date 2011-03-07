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

import ast
import random

from common import const, utils
from common.locations import Locations

Command = Locations.Command

class SimpleMathsCommand(Command):
	name = 'maths'
	rank = const.RANK_USER
	file = __file__
	use_global_context = True

	@classmethod
	def thread(cls, bot):
		user, cmd = yield

		if cmd == 'go':
			SimpleMathsHook.go(bot)
		elif cmd == 'nogo':
			SimpleMathsHook.nogo(bot)



class SimpleMathsHook(Locations.EvMsg):
	file = __file__
	use_global_state = True

	equation = ''
	answer = 0
	running = False
	timer = None

	max_div_tries = 20

	@classmethod
	def thread(cls, bot):
		user, msg = yield

		if cls.running:
			answer = msg['body']
			if answer.isdigit():
				answer = int(answer)
				if answer == cls.answer:
					bot.sendtoall(
						"Congratulations to %s for correctly "
						"answering %s = %d" % (
							utils.getname(msg['from']),
							cls.equation, answer
						)
					)
					cls.timer = bot.timers.add_timer(3000, cls.new, bot)

	@classmethod
	def make_equation(cls):
		sign = random.choice(['+', '-', '*', '/'])
		numbers = [random.randint(1, 24) for x in range(2)]
		if sign == '-' and numbers[0] < numbers[1]:
			numbers.reverse()
		elif sign == '/':
			tries = 0
			answer = 0.1
			while tries < cls.max_div_tries or not answer.is_integer():
				answer = float(numbers[0] / numbers[1])
				if answer.is_integer() and numbers[0] != answer != 1:
					break
				tries += 1
				numbers = [random.randint(1, 24) for x in range(2)]
		elif sign == '*':
			while (numbers[0] * numbers[1]) > 100:
				numbers = [random.randint(1, 12) for x in range(2)]

		return '%s %s %s' % (numbers[0], sign, numbers[1])

	@classmethod
	def go(cls, bot):
		cls.equation = cls.make_equation()
		cls.answer = eval(cls.equation)
		cls.running = True

		bot.sendtoall("It's time for SIMPLEMATHS!")
		bot.sendtoall("The equation is: %s = ?" % cls.equation)

	def new(cls, bot):
		cls.equation = cls.make_equation()
		cls.answer = eval(cls.equation)

		bot.sendtoall("The equation is: %s = ?" % cls.equation)

	@classmethod
	def nogo(cls, bot):
		cls.equation = ''
		cls.answer = 0
		cls.running = False
		if cls.timer is not None:
			bot.timers.remove_timer(cls.timer)

		bot.sendtoall("No more SIMPLEMATHS!")
		bot.sendtoall("Thanks for playing!")
