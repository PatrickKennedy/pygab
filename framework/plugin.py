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

import	os
import	sys
import	traceback

from	common	import const, mounts, utils
from	common.ini	import iMan


class PluginFramework(object):
	"""

	Easily integrate plugins into any bot.

	"""

	def __init__(self):
		#Plugin hashing dictionary
		self._pluginhash = {}
		self.pluginpaths = [utils.get_module(), '']

	def get_plugin_path(self, name):
		"""

		Return the first valid path, other wise return None if no path was found.

		"""
		for path in self.gen_plugin_paths(self.pluginpaths, name):
			return path
		else:
			return None


	def gen_plugin_paths(self, plugin_paths, name):
		"""

		Generate valid plugin paths.

		"""
		for folder in plugin_paths:
			plug_path = os.path.abspath(
				os.path.join('.', folder, 'plugins','plugin_%s.py' % name)
			)
			if os.path.exists(plug_path):
				yield plug_path

	def load_plugins(self, plugins):
		"""load_plugins(plugins: list<str>) -> list

		Load each plugin name passed in `plugins`
		Return a list of successfully loaded plugins.

		"""
		loaded = []
		for plugin_name in plugins:
			#TODO: Support loading multiple
			plug_path = self.get_plugin_path(plugin_name)
			if not plug_path:
				self.error(self.active_user, 'The plugin "plugin_%s.py" could not be found.' % plugin_name)
				continue

			try:
				if self._load_plugin(plugin_name, plug_path):
					loaded.append(plugin_name)
			except:
				traceback.print_exc()
				print '\n'
				self._unload_plugin(plug_path)
				utils.debug('plugins', 'There was an error importing the plugin. A report has been logged.')

				utils.confirmdir("errors")
				with file(os.path.join('.', 'errors', "PluginError-%s.log" % self.module), "a+") as pluglog:
					print >>pluglog, "\n Plugin error log for: ", plugin_name
					traceback.print_exc(None, pluglog)
				continue

		return loaded

	def _load_plugin(self, name, path_):
		"""load_plugin(path_: str) -> bool

		Load `path_` and attempt to execute.
		Return True if it was executed.
		Return False if no changes were made (ie. not executed).

		"""

		with open(path_, "r") as f:
			a = f.read()
		# Skip plugins that haven't been updated.
		if self._pluginhash.get(name, 0) == hash(a):
			return False

		# Replicate __file__ in the plugin, since it isn't set by the
		# interpreter when it executes a string.
		# We're using __file__ to know what command classes to unload.
		plugin = {'__file__':path_}
		exec a in plugin
		# If the plugin has any initialization to be run, handle that here.
		initializer = mounts.PluginInitializers.plugins.get(path_)
		if initializer:
			initializer(self).initialize()

		utils.debug('core', "Loading Plugin (%s)" % path_)
		self._pluginhash[name] = hash(a)
		return True

	def unload_plugins(self, plugins):
		"""unload_plugins(plugins: list<str>) -> list

		Unload each plugin name passed in `plugins`
		Return a list of successfully unloaded plugins.

		"""

		unloaded = []
		for plugin_name in plugins:
			if plugin_name not in self._pluginhash:
				self.error(self.active_user, "The %s plugin hasn't been loaded or was"
						   " misspelled." % plugin_name)
				continue

			plugin_path = self.get_plugin_path(plugin_name)
			if not plugin_path:
				self.error(self.active_user, "The %s plugin is loaded but I can't find the"
						   " file to unload it." % plugin_name)
				continue

			self._unload_plugin(plugin_path)
			del self._pluginhash[plugin_name]
			unloaded.append(plugin_name)

		return unloaded

	def _unload_plugin(self, path_):
		utils.debug('core', "Unloading Plugin (%s)" % path_)
		initializer = mounts.PluginInitializers.plugins.get(path_)
		if initializer:
			if isinstance(initializer, type):
				initializer.remove(initializer)
			else:
				initializer.__exit__()

		for cmd in mounts.CommandMount.get_plugin_list(file=path_):
			if isinstance(cmd, type):
				cmd.remove(cmd)
			else:
				cmd.__exit__()

		for hook in mounts.HookMount.get_plugin_list(file=path_):
			if isinstance(hook, type):
				hook.remove(hook)
			else:
				hook.__exit__()

	def hook(self, loc, *args, **kwargs):
		'''hook(str, loc, *args, **kwargs) -> bool

		Hooks at 'loc' are processed in this order.
		Run all critical hooks, return False for hooks that return True.
		Run all persistant hooks, ingoring return values.
		Run all non-persistant hooks, return false for hooks that return True.

		'''
		# Multiple plugins can register hooks, the first one to
		# return True causes all further processing of that hook
		for hook in mounts.HookMount.get_plugin_list(loc=loc):
			# Class objects are types while class instances are not.
			# This means if the hook is not a type it's already been initialized
			if isinstance(hook, type):
				# Initialize the hook to define it's default variables.
				hook = hook(self)

			# Process the next frame of the hook's generator.
			if hook.process(*args, **kwargs) is True:
				return False

		return True

		for hook in mounts.HookMount.get_plugin_list(
			loc=loc, critical=True, persist=None):
			if hook(self).run(*args, **kwargs):
				return False

		for hook in mounts.HookMount.get_plugin_list(
			loc=loc, persist=True, critical=None):
			hook(self).run(*args, **kwargs)

		for hook in mounts.HookMount.get_plugin_list(
			loc=loc, persist=None, critical=None):
			if hook(self).run(*args, **kwargs):
				return False
		return True

	def command(self, user, msg, whisper=False):
		args = ''
		if " " in msg:
			cmd, args = msg.split(" ",1)
			cmd = cmd.lower()
		else:
			cmd = msg.strip().lower()
		#FIXME: This is a work around for shlex's poor unicode support.
		args = args.encode(sys.getdefaultencoding(),"replace")

		if utils.getname(user).lower() in iMan.config.users.banned:
			return

		try:
			cmd_func = mounts.CommandMount.plugins.get(cmd)
			if not cmd_func:
				self.error(user, "Unknown command, try !help")
				return

			# Class objects are types while class instances are not.
			# When cmd_func is not a type it's already been initialized
			if isinstance(cmd_func, type):
				# Initialize the hook to define it's default variables.
				cmd_func = cmd_func(self)

			#assert isinstance(cmd, CommandMount)

			authorized = True
			if cmd_func.rank == const.RANK_USER:
				pass

			elif cmd_func.rank == const.RANK_MOD:
				if not utils.ismod(user) or not utils.isadmin(user):
					authorized = False
					self.error(user, "You must be a moderator to use that command.")

			elif cmd_func.rank == const.RANK_ADMIN:
				if not utils.isadmin(user):
					authorized = False
					self.error(user, "You must be an admin to use that command.")

			else:
				authorized = False
				self.error(user, "Unknown command, try !help")

			if authorized:
				cmd_func.process(user, args, whisper)

		except const.CommandHelp, args:
			self.sys(user, cmd_func.__doc__)

		except const.CommandError, args:
			self.error(user, 'There was a problem with your command: %s Sorry!' % cmd)

		except StopIteration:
			pass

		except:
			print 'An error happened in the command: %s' % cmd
			traceback.print_exc()
			self.error(user, 'There was a problem with your command (%s) Sorry!' % cmd)
