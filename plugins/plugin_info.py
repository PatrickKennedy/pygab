"""
|===== Conference Bot Plugin ============
|= Information Commands
|===== By: ==============================
|= Patrick Kennedy
|===== Current Version: =================
|= 1.0
|===== Description: =========================================
|= Various commands designed to display information about the bot.
|===== Additional Comments: =================================
|=
|============================================================"""

import	argparse
import	shlex

from	ini		import	iMan
from	utils	import	*
module = get_module()
exec(get_import(mod=module, from_=['utils']))
try:
	exec(get_import(mod=module, from_=['mounts'], import_=['CommandMount']))
except ImportError, e:
	print e

class Help(CommandMount):
	name = 'help'
	rank = CommandMount.RANK_USER
	file = __file__

	help_parser = argparse.ArgumentParser(prog='!help', add_help=False,
		epilog='''Options in <>'s are required.\n\
			Options in []'s are optional.\n\
			Don't include backets.''')
	help_parser.add_argument('cmd', const=True, nargs='?',
		metavar='command -', help='Display detailed information about a command.')

	__doc__ = """Display this help message.\n%s""" % (help_parser.format_help())

	def __init__(self, parent):
		self.parent = parent

	def __exit__(self):
		CommandMount.remove(self.__class__)

	def run(self, user, args):
		options = self.help_parser.parse_args(shlex.split(args))
		self.cmd_help(user, options)

	def cmd_help(self, user, args):
		if args.cmd:
			if args.cmd in CommandMount.plugins:
				self.parent.sendto(user, CommandMount.plugins[args.cmd].__doc__)
			else:
				self.parent.error(user, "I don't know that command (%s). \
					Please check your spelling." % args.cmd)
			return

		reply = "Commands prefixes: %s\n\n\
			----\n\n" % (iMan.config.system.commandprefix)

		user_cmd_list = []
		mod_cmd_list = []
		admin_cmd_list = []
		for cmd in CommandMount.plugins.itervalues():
			# Skip commands if a user doesn't match the command's rank.
			#if cmd.rank == CommandMount.RANK_USER:

			if cmd.rank == CommandMount.RANK_MOD:
				if has_rank(user, 'mod') or has_rank(user, 'admin'):
					mod_cmd_list.append(cmd)

			elif cmd.rank == CommandMount.RANK_ADMIN:
				if has_rank(user, 'admin'):
					admin_cmd_list.append(cmd)

			else:
				user_cmd_list.append(cmd)

		for cmd in user_cmd_list:
			try:
				reply += "%s | %s\n" % (cmd.name, cmd.__doc__.split('\n')[0])
			except:
				continue

		if mod_cmd_list:
			reply = reply + "\nModerator commands:\n"
			for cmd in mod_cmd_list:
				try:
					reply += "%s | %s\n" % (cmd.name, cmd.__doc__.split('\n')[0])
				except:
					continue
		if mod_cmd_list:
			reply = reply + "\nAdmin commands:\n"
			for cmd in admin_cmd_list:
				try:
					reply += "%s | %s\n" % (cmd.name, cmd.__doc__.split('\n')[0])
				except:
					continue

		self.parent.sendto(user,reply)


class Names(CommandMount):
	name = 'w'
	rank = CommandMount.RANK_USER
	file = __file__

	name_parser = argparse.ArgumentParser(prog='!w', add_help=False,
	epilog='''Key:\n* '@' - Admin\n* '%%' - Mod\n* '-' - Away\n* '!' - Busyn\* '#' - Banned''')
	name_parser.add_argument('nil', help=argparse.SUPPRESS)

	#Setup the doc string with the help text from the argument parser.
	__doc__ = """List status of users.\n%s""" % (name_parser.format_help())

	def __init__(self, parent):
		self.parent = parent

	def __exit__(self, *args):
		CommandMount.remove(self.__class__)

	def run(self, user, args):
		self.cmd_names(user, args)

	def cmd_names(self, user, args):

		statuses ={
			'admins' : [],
			'online' : [],
			'offline' : [],
			'away' : [],
			'idle' : [],
			'busy' : []
		}

		for i in self.parent.getRoster():
			i = getjid(i)
			name = getnickname(i)
			if name == iMan.config.server.username:
				continue
			jidStatus = self.parent.getJidStatus(i).items()
			if jidStatus != []:
				for who,(status,display) in jidStatus:
					if '@' not in unicode(who):
						continue
					if has_rank(who, 'banned'):
							name = "#%s" % name
							continue

					if [(jid, msg) for (jid, (status, msg)) in jidStatus if status in ["online","chat"]]:
						if has_rank(who, 'admin'):
							name = "@%s" % name
							statuses['admins'].append(name)
						elif has_rank(who, 'mod'):
							name = "%"+"%s" % name
							statuses['admins'].append(name)
						else:
							statuses['online'].append(name)
						break

					#Anyone not "available".
					elif [(jid, msg) for (jid, (status, msg)) in jidStatus if status in [u"away",u"dnd",u"xa"]]:
						if status in [u"away",u"xa"]:
							name = "-%s" % name
							statuses['idle'].append(name)
						elif status == u"dnd":
							name = "!%s" % name
							statuses['busy'].append(name)
						break
			else:
				pass#statuses['offline'].append('(%s)' % name)

		# Setup the header with a header for total number of users.
		reply = 'Users: (%s)\n'
		total = 0
		for status, users in statuses.iteritems():
			if not users:
				continue
			reply += '%s: (%s)\n%s\n\n' % (status, len(users), ' '.join(users))
			total += len(users)

		# Tack on the total number of users.
		reply = reply % total

		self.parent.sendto(user, reply)
