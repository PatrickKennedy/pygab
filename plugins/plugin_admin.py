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


import	argparse
import	os
import	shlex
import	sys
import	time

from	datetime	import	datetime

from	common			import argparse, const, mounts, utils
from	common.ini		import	iMan
#from	common.utils	import	*
#module = get_module()
#exec(get_import(mod=module, from_=['utils']))
#try:
#	exec(get_import(mod=module, from_=['mounts'], import_=['CommandMount']))
#except ImportError, e:
#	print e

class Echo(mounts.CommandMount):
	name = 'echo'
	rank = const.RANK_USER
	file = __file__


	def thread(self, user, args, whisper):
		self.parent.sendto(user, args)

class RawMsg(mounts.CommandMount):
	name = 'raw'
	rank = const.RANK_ADMIN
	file = __file__


	def thread(self, user, args, whisper):
		self.parent.sendtoall(args)

class Whisper(mounts.CommandMount):
	name = 'sm'
	rank = const.RANK_ADMIN
	file = __file__


	def thread(self, user, args, whisper):
		target, msg = utils.split_target(args)
		self.parent.sendto(target, msg)

class ToggleCommand(mounts.CommandMount):
	name = 'toggle'
	rank = const.RANK_ADMIN
	file = __file__

	__doc__ = 'Disabled a command without unloading the whole plugin. \n' \
				'Usage: !toggle cmd_name'


	def thread(self, user, names, whisper):
		if ',' in names:
			names = names.split(',')
		else:
			names = [names]
		for name in names:
			name = name.strip()
			cmd = self.plugins.get(name)
			if not cmd:
				self.parent.sendto(user, "Unknown Command: %s" % name)
				return

			if cmd.rank == const.RANK_DISABLED:
				self.parent.sendto(user, 'Command Enabled: %s' % name)
				cmd.rank = cmd.prev_rank
				del cmd.prev_rank
			else:
				self.parent.sendto(user, 'Command Disabled: %s' % name)
				cmd.prev_rank = cmd.rank
				cmd.rank = const.RANK_DISABLED

class HookBlockUser(mounts.HookMount):
	name = 'block'
	loc = [const.LOC_EV_MSG]
	file = __file__
	priority = const.PRIORITY_CRITICAL


	def thread(self, user, args):
		if iMan.loaded('roster') and iMan.roster[utils.getname(user).lower()].has_key('blocked'):
			return True

class IgnoreUser(mounts.CommandMount):
	name = 'ignore'
	rank = const.RANK_ADMIN
	file = __file__

	__doc__ = "Make the bot ignore imput from the user. \n Usage: !block <username>"


	def thread(self, user, target, whisper):
		if not iMan.loaded('roster'):
			self.parent.sendto(user, "The roster isn't loaded. I am unable to block users")
			return

		unix_target = target.lower()
		if iMan.roster.has_key(unix_target):
			if iMan.roster[unix_target].has_key('blocked'):
				self.parent.sendto(user, "%s is already blocked." % target)
				return
			else:
				iMan.roster[unix_target].blocked = True
				self.parent.sendto(user, "I am no longer accepting input from %s." % target)
				return
		else:
			iMan.roster[unix_target].blocked = True
			self.parent.sendto(user, "I am no longer accepting input from %s. NOTE: I don't know who that is." % target)
			return

class UnignoreUser(mounts.CommandMount):
	name = 'unignore'
	rank = const.RANK_ADMIN
	file = __file__

	__doc__ = "Allow the user to interact with the bot. \n Usage: !unblock <username>"


	def thread(self, user, target, whisper):
		if not iMan.loaded('roster'):
			self.parent.sendto(user, "The roster isn't loaded. I am unable to unblock users")
			return

		unix_target = target.lower()
		if iMan.roster.has_key(unix_target):
			if not iMan.roster[unix_target].has_key('blocked'):
				self.parent.sendto(user, "%s is not blocked." % target)
				return
			else:
				del iMan.roster[unix_target].blocked
				self.parent.sendto(user, "I am now accepting input from %s." % target)
				return
		else:
			self.parent.sendto(user, "I don't know who %s is, therefore they cannot have been blocked." % target)
			return

class LoadParser(object):
	rank = const.RANK_ADMIN
	file = __file__

	load_parser = argparse.ArgumentParser(prog='!(re|un)load', add_help=False)
	load_parser.add_argument(
		'extra',
		default=False, nargs='?',
		metavar='command', help='Start, stop, restart'
	)
	load_parser.add_argument(
		'-a', '--all',
		action='store_true',
		help='Equvilant to -p -i'
	)
	load_parser.add_argument(
		'-p', '--plugin',
		const=True, default=False, nargs='?',
		metavar='plugin_name', help='(re|un)load plugins'
	)
	load_parser.add_argument(
		'-i', '--ini',
		const=True, default=False, nargs='?',
		metavar='ini_name', help='(re|un)load inis'
	)


class Reload(mounts.CommandMount, LoadParser):
	name = 'reload'

	__doc__ = """Reload parts of the bot.\n%s""" % (LoadParser.load_parser.format_help())


	def thread(self, user, args, whisper):
		options = self.load_parser.parse_args(shlex.split(args.lower()))

		if options.extra:
			self.parent.error(user, "Please use one of the arguments. Ex. -p user, -i roster")
			return

		if options.ini is True or options.all:
			iMan.readall()
			self.parent.sendto(user, 'I have read all ini\'s')
		elif options.ini:
			iMan[options.ini].read()
			self.parent.sendto(user, 'I have read the ini (%s)' % options.ini)

		if options.plugin is True or options.all:
			plugins_to_load = self.parent._pluginhash.keys()
			if False:
				plugins_to_load = iMan.config.system.plugins
				if isinstance(plugins_to_load, basestring):
					plugins_to_load = plugins_to_load.split(' ')
		elif options.plugin:
			plugins_to_load = [options.plugin]

		plugins_to_load = [x for x in plugins_to_load
						   if self.parent.plugin_changed(x)]
		self.parent.unload_plugins(plugins_to_load)
		loaded = self.parent.load_plugins(plugins_to_load)

		if options.plugin or options.all:
			if not loaded:
				self.parent.sendto(user, "No plugins required reloading.")
			else:
				self.parent.sendto(user, "Plugins reloaded: %s" % ", ".join(loaded))

	# When we're reloading THIS command is active and can't be unloaded.
	def __exit__(*args): pass

class Load(mounts.CommandMount, LoadParser):
	name = 'load'

	__doc__ = """Load parts of the bot.\n%s""" % (LoadParser.load_parser.format_help())


	def thread(self, user, args, whisper):
		options = self.load_parser.parse_args(shlex.split(args.lower()))

		if options.extra:
			self.parent.error(user, "Please use one of the arguments. Ex. -p user, -i roster")
			return

		if options.ini is True:
			self.parent.error(user, "You must pass the name of an ini to load.")
		elif options.ini:
			if iMan.load(options.ini):
				self.parent.sendto(user, 'I have successfully loaded the ini (%s)' % options.ini)
			else:
				self.parent.sendto(user, 'I can\'t load the ini (%s)' % options.ini)

		if options.plugin is True:
			self.parent.error(user, "You must pass the name of a plugin to load.")
		elif options.plugin:
			loaded = self.parent.load_plugins([options.plugin])

			if not loaded:
				self.parent.sendto(user, "The %s plugin is already loaded." % options.plugin)
			else:
				self.parent.sendto(user, "Plugins loaded: %s" % ", ".join(loaded))



class Unload(mounts.CommandMount, LoadParser):
	name = 'unload'

	__doc__ = """Unload parts of the bot.\n%s""" % (LoadParser.load_parser.format_help())


	def thread(self, user, args, whisper):
		options = self.load_parser.parse_args(shlex.split(args.lower()))

		if options.extra:
			self.parent.error(user, "Please use one of the arguments. Ex. -p user, -i roster")
			return

		if options.ini is True:
			self.parent.error(user, "You must pass the name of an ini to unload.")
		elif options.ini:
			if iMan.unload(options.ini):
				self.parent.sendto(user, 'I have successfully unloaded the ini (%s)' % options.ini)
			else:
				self.parent.sendto(user, 'I can\'t unload the ini (%s)' % options.ini)


		if options.plugin is True:
			self.parent.error(user, "You must pass the name of a plugin to unload.")
		elif options.plugin:
			names = [options.plugin]
			unloaded = self.parent.unload_plugins(names)
			self.parent.sendto(user, "Plugins unloaded: %s" % ", ".join(unloaded))

	# In the event we unload this plugin THIS command is active and can't be unloaded.
	def __exit__(*args): pass
