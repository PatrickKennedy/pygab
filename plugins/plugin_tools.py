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

import random
import re

from common import const, utils
from common.locations import Locations
from common.pyni import Config

Command = Locations.Command

class Calc(Command):
	name = 'calc'
	rank = const.RANK_USER
	file = __file__

	__doc__ = "Calculate a mathematical expression. \nSupports variables x, y, and z. \nEx. x=5;y=2;x**y"

	filter = re.compile('[^\d()*%+-/\sxyz=;]*')

	@staticmethod
	def format(e):
		"""Format the expression to set the final value to 'a'"""
		if ';' in e:
			x = e.rfind(';')
			e = e[:x+1]+'a='+e[x+1:]
		else:
			e = 'a='+e
		return e

	@classmethod
	def thread(cls, bot):
		"""Calculate an equation.

		Usage: )calc <math equation>
		Example: /calc ((1 + 2) * 2) / 2

		"""
		user, e = yield

		if not e:
			raise const.CommandHelp("Missing equation")
		username = utils.getname(user)
		answer = {}

		e = e.replace('^', '**')
		e = cls.filter.sub('', e)

		try:
			eval(compile(cls.format(e), 'Calc.py', 'single'), {}, answer)
		except SyntaxError:
			bot.error(user, "Please check your equation for errors.")
			return
		except ZeroDivisionError:
			if False or whispered:
				bot.sendto(user, 'Why are you hiding your attempts to '
								   'crash the Universe? Try that where everyone '
								   'can see it, foo!')
			else:
				bot.sendtoall('%s just tried to divide by zero. Stone him.' % username)
			return

		answer = answer['a']
		if False and bot.was_whispered:
			bot.sendto(user, '"%s" => %s' % (e, answer))
		else:
			bot.sendtoall('%s: "%s" => %s' % (username, e, answer))

class Hack(Command):
	name = 'hack'
	rank = const.RANK_USER
	file = __file__

	@classmethod
	def thread(cls, bot):
		user, args = yield
		bot.error(user, "Your IP has been logged.")

class Roll(Command):
	name = 'roll'
	rank = const.RANK_USER
	file = __file__

	__doc__ = "Rolls a random number. " \
		   "Usage: !roll [<number of dice>[d<number of sides>]]"

	@classmethod
	def thread(self, bot):
		""""""
		dice = 1
		sides = 6
		rolls = []
		percentile = False
		rounded_percentile = False
		result_msg = ''

		user, args = yield

		if args:
			if 'd' in args:
				dice, sides = args.split('d', 2)
				if ' ' in sides:
					sides = sides[:sides.find(' ')]
			else:
				dice = args

			if sides == '%':
				percentile = True
				# Only roll for the tens place.
				if dice == '1':
					rounded_percentile = True
				sides = 10
				dice = 2

			try:
				dice = int(dice)
				sides = int(sides)
			except:
				bot.error(user, self.__doc__)
				return

			dice = max(1, min(int(dice), 100))
			sides = max(2, min(int(sides), 100))
			#if dice > 5:
			#	dice = 5
			#	bot.error(user, "The number of dice has been set to 5.")
			#elif dice < 1:
			#	dice = 1
			#	bot.error(user, "The number of dice has been set to 1.")

			#if sides > 100:
			#	sides = 100
			#	bot.error(user, "The number of sides has been set to 100.")
			#elif 2 != sides < 4:
			#	sides = 4
			#	bot.error(user, "The number of sides has been set to 4.")

		rolls = [random.randint(1, sides) for x in range(dice)]

		if percentile:
			# Adjust for percentile dice which are 0-9
			rolls[0] -= 1
			rolls[1] -= 1
			# Handle double zeros which are 100%
			if rolls[0] == 0 == rolls[1]:
				total = 100
			else:
				if rounded_percentile:
					rolls[1] = 0
				total = (rolls[0]*10) + rolls[1]
			result_msg = "rolled %d%%" % (total)

		elif sides != 2:
			total = 0
			for x in rolls:
				total += x
			result_msg = "rolled %d (%s) with %dd%d" % (
				total, ', '.join(['%s' % i for i in rolls]), dice, sides)

		# If sides == 2, handles coin flips.
		elif dice == 1:
			result_msg = "flipped a coin that landed on %s" % (
				rolls[0] == 1 and "Heads" or "Tails")
		else:
			heads = 0
			tails = 0
			for x in rolls:
				if x == 1:
					heads += 1
				else:
					tails += 1

			result_msg = ("flipped a coin %d times which landed on Heads %d "
			"times and Tails %d times." % (dice, heads, tails))

		if False and bot.was_whispered:
			bot.sendto(user, 'You %s' % result_msg)
		else:
			bot.sendtoall('%s %s' % (utils.getname(user), result_msg))

		return
		self.systoall("%s rolls %s with %s %s-sided %s\n%s" % (
				getnickname(user),
				reduce(operator.add, total),
				dice == 1 and "a" or dice,
				sides,
				dice and "die" or "dice",
				reduce((lambda x, y: str(x) + " | " + str(y)), total)
			)
		)
