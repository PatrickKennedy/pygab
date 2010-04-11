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

import logging
import logging.handlers
import os
import re
import sys
import traceback

from	common	import const, mounts, utils
from	common.ini	import iMan

_plugin_log = logging.getLogger('pygab.plugins')
_handler = logging.handlers.RotatingFileHandler(
	os.path.join('.', utils.get_module(), 'plugin_errors.log'),
	maxBytes=256000, backupCount=3, encoding='utf-8', delay=True
)
_handler.setLevel(logging.ERROR)
_plugin_log.addHandler(_handler)

def attach_hooks(hook_name=''):
	"""Attach both pre- and -post hooks.

	"""
	def decorator(func):
		def wrapper(self, *args):
			self.hook('%s_pre' % (hook_name or func.__name__), *args)
			func(self, *args)
			self.hook('%s_post' % (hook_name or func.__name__), *args)
		return wrapper
	return decorator


def attach_post_hook(hook_name=''):
	"""Attach only the -post hook.

	For use if there is a critical check before the pre- hook which requires it
	to be defined within the function itself.

	"""
	def decorator(func):
		def wrapper(self, *args):
			func(self, *args)
			self.hook('%s_post' % (hook_name or func.__name__), *args)
		return wrapper
	return decorator


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

	def plugin_changed(self, plugin_name, plugin_source=None):
		"""Return True if a plugin's source has changed"""

		if not plugin_source:
			path_ = self.get_plugin_path(plugin_name)
			with open(path_, "r") as f:
				plugin_source = f.read()

		return self._pluginhash.get(plugin_name, 0) != hash(plugin_source)

	def load_plugins(self, plugins):
		"""load_plugins(plugins: list<str>) -> list

		Load each plugin name passed in `plugins`
		Return a list of successfully loaded plugins.

		"""
		loaded = []
		for plugin_name in plugins:
			#TODO: Support loading multiple plugins on top of each other
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
				#utils.debug('plugins', 'There was an error importing the plugin. A report has been logged.')
				_plugin_log.error('There was an error importing %s\n%s' % (plugin_name, traceback.format_exc()))

				#utils.confirmdir("errors")
				#with file(os.path.join('.', 'errors', "PluginError-%s.log" % self.module), "a+") as pluglog:
				#	print >>pluglog, "\n Plugin error log for: ", plugin_name
				#	traceback.print_exc(None, pluglog)
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
		if not self.plugin_changed(name, a):
			return False

		# Replicate __file__ in the plugin, since it isn't set by the
		# interpreter when it executes a string.
		# We're using __file__ to know what command classes to unload.
		plugin = {'__file__':path_}
		exec compile(a, 'plugin_%s.py' % name, 'exec') in plugin
		# If the plugin has any initialization to be run, handle that here.
		initializer = mounts.PluginInitializers.plugins.get(path_)
		if initializer:
			initializer(self).initialize()

		#utils.debug('core', "Loading Plugin (%s)" % path_)
		_plugin_log.info("Loading Plugin (%s)" % path_)
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

		All hooks at 'loc' are processed with the passed args.
		If any hook returns a True value hook will return True to signal the
		calling function to break execution.

		'''

		# If True the calling function should break execution
		break_ = False

		for hook in mounts.HookMount.get_plugin_list(loc=loc):
			# Class objects are types while class instances are not.
			# This means if the hook is not a type it's already been initialized
			if isinstance(hook, type):
				# Initialize the hook to define it's default variables.
				hook = hook(self)

			# Process the next frame of the hook's generator.
			break_ |= bool(hook.process(*args, **kwargs))

		return break_


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

	def command_depreciated(self, user, text, msg):
		args = ''
		text = text.strip()
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
			self.redirect_to_user = m.group('user')
			cmd = self.redirect_check.sub('', cmd)

		# [<name>] Prefix. Replaces the calling user with the jid of <name>.
		m = self.mimic_check.search(cmd)
		if m and utils.isadmin(user):
			user = utils.getjid(m.group('user'))
			cmd = self.mimic_check.sub('', cmd)

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
			if cmd_func.rank in [const.RANK_USER, const.RANK_HIDDEN]:
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
				cmd_func.process(user, args)

		except const.CommandHelp, args:
			self.sys(user, cmd_func.__doc__)

		except const.CommandError, args:
			self.error(user, 'There was a problem with your command: %s Sorry!' % cmd)

		except StopIteration:
			pass

		except Exception, e:
			print 'An error happened in the command: %s' % cmd
			traceback.print_exc()
			self.error(user, 'There was a problem with your command: %s. Sorry! \n'
						'Exception: %r' % (cmd, e))
