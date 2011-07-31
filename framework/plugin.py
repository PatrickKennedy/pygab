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

from common	import const, mounts, utils
from common.ini	import iMan
from common.locations import Locations

plugin_log = logging.getLogger('pygab.plugins')
_handler = logging.handlers.RotatingFileHandler(
	os.path.join('.', utils.get_module(), 'plugin_errors.log'),
	maxBytes=256000, backupCount=3, encoding='utf-8', delay=True
)
_handler.setLevel(logging.ERROR)
plugin_log.addHandler(_handler)


class PluginFramework(object):
	"""

	Easily integrate plugins into any bot.

	"""

	def __init__(self, host, folder_name="plugins", name_format="plugin_%s.py"):
		self.host = host
		#Plugin hashing dictionary
		self._pluginhash = {}
		self.loaded = set() # A unique list
		self.search_paths = [utils.get_module(), '']
		self.folder_name = folder_name
		self.name_format = name_format

	def path_for(self, name):
		"""

		Return the first valid path, other wise return None if no path was found.

		"""
		for path in self.paths_for(name):
			return path
		else:
			return None

	def paths_for(self, name, search_paths=None):
		"""

		Generate valid plugin paths.

		"""
		search_paths = search_paths or self.search_paths

		for folder in search_paths:
			path = os.path.abspath(
				os.path.join(
					'.', folder, self.folder_name,
					self.name_format % name
				)
			)
			if os.path.exists(path):
				yield path

	def changed(self, name):
		"""

		Return True if at least one file related to the plugin has changed.

		"""
		# Returning a generator means the check is at most O(n) operations
		# rather than always being O(n).
		for path in self.files_changed(name):
			return True
		return False

	def files_changed(self, name):
		"""

		Return a generator list of changed files related to a plugin.

		"""
		return (
			path
			for path in self.paths_for(name)
			if self.file_changed(path)
		)

		#for path in self.paths_for(name):
		#	if self.file_changed(path):
		#		yield path

	def file_changed(self, path, source=None):
		"""Return True if a plugin's specific has changed"""

		if not source:
			with open(path, "r") as f:
				source = f.read()

		return self._pluginhash.get(path, 0) != hash(source)

	def load(self, *names):
		loaded = []
		for name in names:
			plugin_log.info("Attempting to load plugin: %s" % name)
			paths = list(self.paths_for(name))
			if not paths:
				plugin_log.warning('The plugin "plugin_%s.py" could not be found.' % name)
				# TODO: Add check to see if the bot is connected before trying to
				# send errors to people.
				if self.active_user:
					self.error(self.active_user, 'The plugin "plugin_%s.py" could not be found.' % name)
				continue

			plugin_namespace = {}

			successfully_loaded = 0
			for path in paths:
				plugin_namespace["__file__"] = path
				try:
					self._load(name, path, plugin_namespace)
				except:
					plugin_log.exception('There was an error importing %s' % path)
					self._unload(name, path)
				else:
					successfully_loaded += 1

			# If the plugin has any initialization to be run, handle that here.
			initializer = Locations.Initializers.activities.get(name)
			if initializer:
				initializer(self.host).process()

			if successfully_loaded:
				loaded.append(name)
		return loaded

	def _load(self, name, path, namespace):
		"""load_plugin(path_: str) -> bool

		Load `path` and attempt to execute.
		Return:
			True if it was executed.
			False if no changes were made (ie. not executed).

		"""

		with open(path, "r") as f:
			a = f.read()
		# Skip plugins that haven't been updated.
		if not self.file_changed(path, a):
			return False

		# Replicate __file__ in the plugin, since it isn't set by the
		# interpreter when it executes a string.
		# __file__ lets us know what hooks to unload.
		#exec(compile(a, 'plugin_%s.py' % name, 'exec'), namespace)
		exec(compile(a, path, 'exec'), namespace)

		#utils.debug('core', "Loading Plugin (%s)" % path_)
		plugin_log.info("Loading Plugin (%s: %s)" % (name, path))
		self._pluginhash[path] = hash(a)
		self.loaded.add(name)
		return True


	def unload(self, *plugins):
		"""unload(plugins: list<str>) -> list

		Unload each plugin name passed in `plugins`
		Return a list of successfully unloaded plugins.

		"""

		unloaded = []
		for name in plugins:
			if name not in self.loaded:
				self.error(self.active_user, "The plugin (%s) hasn't been"
						   " loaded or was misspelled." % name)
				continue

			for path in list(self.paths_for(name)):
				self._unload(name, path)
				del self._pluginhash[path]

			self.loaded.remove(name)
			unloaded.append(name)

		return unloaded

	def _unload(self, name, path):
		plugin_log.info("Unloading Plugin (%s: %s)" % (name, path))
		for location in Locations:
			for activity in location.get_activities_for(path):
				activity.remove()
