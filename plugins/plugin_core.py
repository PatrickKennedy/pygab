#!/usr/bin/env python

import argparse
import logging
import re
import shlex

from common import const, pyni, utils
from common.locations import Locations, Location

from framework import plugin

log = logging.getLogger('pygab.plugin.core')
cmd_log = logging.getLogger('pygab.plugin.core.cmd_dispatch')

class Command(Location):
	"""Register chat commands

	Hooks implementing this location must provide the following attributes:

	=====  =====================================================================
	name   The lower-case name of the command, used to call it.

	rank   The rank a user must be inorder to perform this command.

	file   The absolute path to a file. You should use __file__.

	=====  =====================================================================

	Arguments:
		user - The JID of the calling users
		*args - The string following the command

	"""


class CommandDispatch(Locations.EvMsg):
	name = 'CommandDispatch'
	file = __file__
	use_global_state = True

	# Used to check if the user wants to redirect the output of a command
	# to another user.
	redirect_check = re.compile('\<(?P<user>.*)\>')

	# Used to check if the caller wants to mimic another user.
	mimic_check = re.compile('\[(?P<user>.*)\]')

	@staticmethod
	def is_authorized(cmd_name, user):
		authorized = True
		cmd_class = Command.hooks[cmd_name]
		if cmd_class.rank in [const.RANK_USER, const.RANK_HIDDEN]:
			pass

		elif cmd_class.rank == const.RANK_MOD:
			if not utils.ismod(user) and not utils.isadmin(user):
				authorized = False

		elif cmd_class.rank == const.RANK_ADMIN:
			if not utils.isadmin(user):
				authorized = False

		elif cmd_class.rank == const.RANK_DISABLED:
			authorized = False

		return authorized

	@classmethod
	def thread(cls, bot):
		user, msg = yield
		text = msg['body'].strip()

		# TODO: Replace with the following when I feel like figuring out how
		# best to strip a arbitrary length delimter
		#if not [x for x in iMan.config.system.commandprefix if text.startswith(x)]:
		with pyni.Config(utils.get_module(), 'config') as ini:
			if text[:1] not in ini.system.commandprefix:
				yield False
				return

		# Partition will return args as a blank string if there's no passed args
		cmd, _, args = text[1:].partition(" ")
		cmd = cmd.lower()

		#FIXME: This is a work around for shlex's poor unicode support.
		#args = args.decode('utf-8', 'replace')

		if utils.isadmin(user):
			# <<name>> Prefix. Used by the bot to redirect a whispers output to <name>
			m = cls.redirect_check.search(cmd)
			if m:
				bot.redirect_to_user = utils.getjid(m.group('user'))
				cmd = cls.redirect_check.sub('', cmd)

			# [<name>] Prefix. Replaces the calling user with the jid of <name>.
			m = cls.mimic_check.search(cmd)
			if m:
				user = utils.getjid(m.group('user'))
				cmd = cls.mimic_check.sub('', cmd)

		cmd_func = Command.get_or_init_state(cmd, user.bare, bot)
		if not cmd_func:
			bot.error(user, "Unknown command, try !help")
			return

		if cls.is_authorized(cmd, user):
			try:
				cmd_func.send([user, args])
			except StopIteration:
				Command.clean(cmd, user.bare)
			except Exception as e:
				log.exception('An error happened in the command: %s' % cmd)
				bot.error(user, 'There was a problem with your command: %s. '
								  'Sorry! \nException: %s' % (cmd, e))
		else:
			bot.error(user, "You're not authorized to use that command.")

		#except const.CommandHelp, args:
		#	bot.sys(user, cmd_func.__doc__)
		#
		#except const.CommandError, args:
		#	bot.error(user, 'There was a problem with your command: %s Sorry!' % cmd)

		yield True

class LoadParser(object):
	rank = const.RANK_ADMIN
	file = __file__

	parser = argparse.ArgumentParser(prog='!(re|un)load', add_help=False)
	parser.add_argument(
		'extra',
		default=False, nargs='?',
		metavar='command', help='Start, stop, restart'
	)
	#parser.add_argument(
	#	'-a', '--all',
	#	action='store_true',
	#	help='Equvilant to -p -i'
	#)
	parser.add_argument(
		'-f', '--force',
		action='store_true',
		help='force an action'
	)
	parser.add_argument(
		'-p', '--plugin',
		const=True, default=False, nargs='?',
		metavar='plugin_name', help='(re|un)load plugins'
	)
	#parser.add_argument(
	#	'-i', '--ini',
	#	const=True, default=False, nargs='?',
	#	metavar='ini_name', help='(re|un)load inis'
	#)


class Reload(Command, LoadParser):
	name = 'reload'

	__doc__ = """Reload parts of the bot.\n%s""" % (LoadParser.parser.format_help())

	@classmethod
	def thread(self, bot):
		user, args = yield

		options = self.parser.parse_args(shlex.split(args.lower()))

		if options.extra:
			bot.error(user, "Please use one of the arguments. Ex. -p mathsgame")
			return

		if options.plugin is True or options.all:
			to_load = bot.plugins.loaded
		elif options.plugin:
			to_load = [options.plugin]

		if options.plugin or options.all:
			if not options.force:
				to_load = [x for x in to_load if bot.plugins.changed(x)]

			bot.plugins.unload(*to_load)
			loaded = bot.plugins.load(*to_load)
			if not loaded:
				bot.sendto(user, "No plugins required reloading.")
			else:
				bot.sendto(user, "Plugins reloaded: %s" % ", ".join(loaded))

class Load(Command, LoadParser):
	name = 'load'

	__doc__ = """Load parts of the bot.\n%s""" % (LoadParser.parser.format_help())

	@classmethod
	def thread(self, bot):
		user, args = yield

		options = self.parser.parse_args(shlex.split(args.lower()))

		if options.extra:
			bot.error(user, "Please use one of the arguments. Ex. -p mathsgame")
			return

		if options.plugin is True:
			bot.error(user, "You must pass the name of a plugin to load.")
		elif options.plugin:
			name = options.plugin
			if name in bot.plugins.loaded:
				bot.sendto(user, "The plugin (%s) is already loaded." % name)
				return

			loaded = bot.plugins.load(name)

			if not loaded:
				bot.sendto(user, "Could not load the plugin (%s) for an unknown reason." % name)
			else:
				bot.sendto(user, "Successfully loaded the plugin (%s)." % name)


class Unload(Command, LoadParser):
	name = 'unload'

	__doc__ = """Unload parts of the bot.\n%s""" % (LoadParser.parser.format_help())

	@classmethod
	def thread(self, bot):
		user, args = yield

		options = self.parser.parse_args(shlex.split(args.lower()))

		if options.extra:
			bot.error(user, "Please use one of the arguments. Ex. -p mathsgame")
			return

		if options.plugin is True:
			bot.error(user, "You must pass the name of a plugin to unload.")
		elif options.plugin:
			unloaded = bot.plugins.unload(options.plugin)
			bot.sendto(user, "Plugins unloaded: %s" % ", ".join(unloaded))
