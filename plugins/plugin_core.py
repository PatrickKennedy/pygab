#!/usr/bin/env python

import logging
import re

from common import const, mounts, utils
from common.ini import iMan

from framework import plugin

log = logging.getLogger('pygab.plugin.core')
cmd_log = logging.getLogger('pygab.plugin.core.cmd_dispatch')

class CommandDispatch(mounts.HookMount):
	name = 'CommandDispatch'
	loc = const.LOC_EV_MSG
	plugin = __name__
	priority = 'e'

	# Used to check if the user wants to redirect the output of a command
	# to another user.
	redirect_check = re.compile('\<(?P<user>.*)\>')

	# Used to check if the caller wants to mimic another user.
	mimic_check = re.compile('\[(?P<user>.*)\]')

	def thread(self, msg):
		text = msg.text.strip()
		user = msg.from_user

		# TODO: Replace with the following when I feel like figuring out how
		# best to strip a dynamic length delimter
		#if not [x for x in iMan.config.system.commandprefix if text.startswith(x)]:
		if text[:1] not in iMan.config.system.commandprefix:
			return False

		text = text[1:]

		args = ''
		if " " in text:
			cmd, args = text.split(" ",1)
			cmd = cmd.lower()
		else:
			cmd = text.lower()

		#FIXME: This is a work around for shlex's poor unicode support.
		#args = unicode(args, 'utf-8', 'replace')
		args = args.encode('utf-8', 'replace')

		# <<name>> Prefix. Used by the bot to redirect a whispers output to <name>
		m = self.redirect_check.search(cmd)
		if m:
			self.parent.redirect_to_user = utils.getjid(m.group('user'))
			cmd = self.redirect_check.sub('', cmd)

		# [<name>] Prefix. Replaces the calling user with the jid of <name>.
		m = self.mimic_check.search(cmd)
		if m and utils.isadmin(user):
			user = utils.getjid(m.group('user'))
			cmd = self.mimic_check.sub('', cmd)

		try:
			cmd_func = mounts.CommandMount.plugins.get(cmd)
			if not cmd_func:
				self.parent.error(user, "Unknown command, try !help")
				return

			# Class objects are types while class instances are not.
			# When cmd_func is not a type it's already been initialized
			if isinstance(cmd_func, type):
				# Initialize the hook to define it's default variables.
				cmd_func = cmd_func(self.parent)

			authorized = True
			if cmd_func.rank in [const.RANK_USER, const.RANK_HIDDEN]:
				pass

			elif cmd_func.rank == const.RANK_MOD:
				if not utils.ismod(user) or not utils.isadmin(user):
					authorized = False
					self.parent.error(user, "You must be a moderator to use that command.")

			elif cmd_func.rank == const.RANK_ADMIN:
				if not utils.isadmin(user):
					authorized = False
					self.parent.error(user, "You must be an admin to use that command.")

			else:
				authorized = False
				self.parent.error(user, "Unknown command, try !help")

			if authorized:
				cmd_func.process(user, args)

		except const.CommandHelp, args:
			self.parent.sys(user, cmd_func.__doc__)

		except const.CommandError, args:
			self.parent.error(user, 'There was a problem with your command: %s Sorry!' % cmd)

		except StopIteration:
			pass

		except Exception, e:
			log.exception('An error happened in the command: %s' % cmd)
			self.parent.error(user, 'There was a problem with your command: %s.'
							  'Sorry! \nException: %r' % (cmd, e))
		finally:
			return True
