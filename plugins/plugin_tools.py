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
import	operator
import	random
import	re
import	shlex
import	threading

from	common			import argparse, const, mounts, utils
from	common.ini		import	iMan
#from	common.utils	import	*

#try:
#	exec(get_import(mod=utils.get_module(), from_=['mounts'],
#		import_=['PluginInitializers', 'HookMount', 'CommandMount']))
#except ImportError, e:
#	print e

class Init(mounts.PluginInitializers):
	name = __file__

	def initialize(self):
		iMan.load('roster', utils.get_module())

	def __exit__(self, *args):
		iMan.unload('roster', save=True)
		mounts.PluginInitializers.remove(self.__class__)

class Calc(mounts.CommandMount):
	name = 'calc'
	rank = const.RANK_USER
	file = __file__

	__doc__ = "Calculate a mathematical expression. \nSupports variables x, y, and z. \nEx. x=5;y=2;x**y"

	def format(self, e):
		if ';' in e:
			x = e.rfind(';')
			e = e[:x+1]+'a='+e[x+1:]
		else:
			e = 'a='+e
		return e


	def thread(self, user, e, whispered):
		"""Calculate an equation.

		Usage: )calc <math equation>
		Example: /calc ((1 + 2) * 2) / 2

		"""
		username = utils.getname(user)
		answer = {}
		try:
			e = re.sub('[^\d()*%+-/\sxyz=;]*', '', e)
			eval(compile(self.format(e), 'Calc.py', 'single'),
				 {}, answer)
		except SyntaxError:
			self.parent.error(user, "Please check your equation for errors.")
			return
		except ZeroDivisionError:
			if whispered:
				self.parent.sendto(user, 'Why are you hiding your attempts to'
								   'crash the Universe? Try that where everyone'
								   'can see it, foo!')
			else:
				self.parent.sendtoall('%s just tried to divide by zero. Stone him.' % username)
			return

		answer = answer['a']
		if whispered:
			self.parent.sendto(user, '"%s" => %s' % (e, answer))
		else:
			self.parent.sendtoall('%s: "%s" => %s' % (username, e, answer))

class Hack(mounts.CommandMount):
	name = 'hack'
	rank = const.RANK_USER
	file = __file__


	def thread(self, user, msg, whispered):
		self.parent.error(user, "Your IP has been logged.")

class Roll(mounts.CommandMount):
	name = 'roll'
	rank = const.RANK_USER
	file = __file__


	def thread(self, user, args, whispered):
		"""Rolls a random number.
		Usage: )dice [[<number of dice>][d<number of sides>]]
		Example: /dice 2d10"""
		dice = 1
		sides = 6
		total = []

		if args:
			if 'd' in args:
				dice, sides = args.split('d', 2)
				if ' ' in sides:
					sides = sides[:sides.find(' ')]
			else:
				dice = args

			if dice.isdigit() and sides.isdigit():
				dice, sides = int(dice), int(sides)
				if dice > 5:
					dice = 5
					self.parent.error(user, "The number of sides has been set to 25.")
				elif dice < 1:
					dice = 1
					self.parent.error(user, "The number of dice has been set to 1.")

				if sides > 100:
					sides = 100
					self.parent.error(user, "The number of sides has been set to 100.")
				elif sides < 4 and sides != 2:
					sides = 4
					self.parent.error(user, "The number of sides has been set to 4.")
			else:
				self.parent.error(user, self.__doc__)
				return


		for i in xrange(dice):
			random.jumpahead(5)
			total.append(random.randrange(1, sides + 1))

		if sides != 2:
			total = reduce(operator.add, total)

		if sides == 2:
			heads = 0
			tails = 0
			for x in total:
				if x == 1:
					heads += 1
				else:
					tails += 1
			if dice > 1:
				self.parent.sendtoall("%s flipped a coin %d times which"
									  " landed on Heads %d times and Tails"
									  " %d times." % (
					utils.getname(user), dice, heads, tails))
			else:
				self.parent.sendtoall("%s flipped a coin that landed on %s" % (
					utils.getname(user), total[0] == 1 and "Heads" or "Tails"))
		else:
			self.parent.sendtoall("%s rolled %d with %dd%d" % (
				utils.getname(user), total, dice, sides))

		if False:
			self.systoall("%s rolls %s with %s %s-sided %s\n%s" % (
					getnickname(user),
					reduce(operator.add, total),
					dice == 1 and "a" or dice,
					sides,
					dice and "die" or "dice",
					reduce((lambda x, y: str(x) + " | " + str(y)), total)
				)
			)
