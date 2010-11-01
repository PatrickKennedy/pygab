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

from framework.pluginregistry import Locations, PluginRegistry

__all__ = ['thread_base', 'PluginInitializers' ,'CommandMount', 'HookMount']

def thread_base(fn):
	def thread():
		result = None
		while 1:
			try: args = (yield result)
			except GeneratorExit: raise

			if args is None:
				result = None
				continue
			result = False

			result = fn(*args)
	return thread

class PluginInitializers:
	"""Stores Initalization classes which run when the plugin is loaded.

	Plugins implementing this mount should provide the following attributes:

	=====  =====================================================================
	name   The path to the plugin. You may use __file__.
		   (The base class for each mount stores classes by their name attribute
		   so we use it here so we don't have to iterate over the dictionary
		   when we unload the plugin.)

	=====  =====================================================================


	Plugins implementing this mount should also provide the following functions:

	=========  =================================================================
	__init__   This function gets passed an instance of the bot.

	__exit__   No arguments are passed to this function.

	=========  =================================================================


	"""
	__metaclass__ = PluginRegistry

	def __init__(self, parent):
		self.parent = parent
		self.plugins[self.name] = self


class CommandMount:
	"""Mount point for bot commands normal users can perform.

	Plugins implementing this mount should provide the following attributes:

	=====  =====================================================================
	name   The name of the command, used to call it.

	rank   The rank a user must be inorder to perform this command.

	file   The absolute path to a file. You are able to use __file__.

	=====  =====================================================================


	Plugins implementing this mount should also provide the following functions:

	=========  =================================================================
	__init__   This function gets passed an instance of the bot.
				- Predefined to define self.parent as the instance of the bot.

	__exit__   No arguments are passed to this function.
				- Predefined to remove the class from the registry.

	   run     run gets passed two arguments:
	            - a JID object of the user calling the command
	            - a string object containing whatever the user said.

	=========  =================================================================


	"""
	__metaclass__ = PluginRegistry

	def __init__(self, parent):
		self.parent = parent

		# Initalize the plugin's thread
		self.init_thread()
		# Replace the class object with this instance
		self.plugins[self.name] = self

	def init_thread(self):
		global thread_base
		self._thread = thread_base(self.thread)()
		self._thread.send(None)

	def process(self, user, msg):
		try:
			self._thread.send((user, msg))
		except StopIteration:
			# A stop iteration typically means the thread threw an error
			# We will see this after the error is thrown so we want to restart
			# the thread, and then we'll reraise the StopIteration.
			self.init_thread()
			self._thread.send((user, msg))
			raise
		except GeneratorExit:
			CommandMount.remove(self)

	def __exit__(self, *args):
		self._thread.close()
		CommandMount.remove(self)

class HookMount:
	"""Mount point for hooks into various processes.

	Each hook location calls any available classes. If a hook returns True then
	all futher processing of hooks and code after the hook location is stopped.

	Plugins implementing this mount should provide the following attributes:

	========  =================================================================
	name      Not used but still needed. Don't ask.

	loc       The location of the hook to be run.
			  Locations are listed in /common/const.py

	file      The absolute path to a file. You are able to use __file__.

	priority  Hooks are processed in decending order based on their priority.
			  Priorities are defined in /common/const.py.
			  The default priorities are Critical, Persistant, and Normal

	========  =================================================================


	Plugins implementing this mount should also provide the following functions:

	=========  =================================================================
	__init__   This function gets passed an instance of the bot.
				- Predefined to define self.parent as the instance of the bot,
				  self.whispered as a boolean, and replace self.thread with an
				  initalized version of itself.

	__exit__   No arguments are passed to this function.
				- Predefined to remove the class from the registry.

	 process   The number of arguments passed to run vary per location.
	           Hook locations should document what they pass.
			    - Predefined to send two arguments to the thread.

	 thread    The hook's generator which acts as a thread. It will be initalized
	           when the class is initalized and passed new variables via send().
	           Reference: http://www.ibm.com/developerworks/linux/library/l-pythrd.html

	=========  =================================================================

	"""

	__metaclass__ = PluginRegistry

	def __init__(self, parent):
		self.parent = parent

		# Initalize the plugin's thread
		self.init_thread()
		# Replace the class object with this instance
		self.plugins[self.name] = self

	def init_thread(self):
		global thread_base
		self._thread = thread_base(self.thread)()
		#self._thread = self.thread()
		self._thread.send(None)

	@staticmethod
	def sort(iter):
		"""Sort decending by each item's priority attribute."""
		iter.sort(key=(lambda x: x.priority), reverse=True)
		return iter

	def process(self, *args):
		try:
			return self._thread.send(args)
		except StopIteration:
			# A stop iteration typically means the thread threw an error
			# We will see this after the error is thrown so we want to restart
			# the thread, and then we'll reraise the StopIteration.
			self.init_thread()
			return self._thread.send(args)
			raise
		except GeneratorExit:
			HookMount.remove(self)

	def __exit__(self, *args):
		self._thread.close()
		HookMount.remove(self)

class Location:
	"""Provides access to locations and standard functions.

	Locations implementing this mount should provide the following attributes:

	========  ==================================================================
	__doc__   Please provide information on what args are passed to the handler
			  and what the expected behavior upon returning a True truth value
			  should be (e.g. consume message in LocEvMsg).
	========  ==================================================================

	"""
	#__metaclass__ = Locations

	def __init__(self, parent):
		self.parent = parent

		# Replace the class object with this instance
		self.hooks[self.__name__] = self

	def __call__(self, *args, **kwargs):
		try:
			self.process(*args, **kwargs)
		except:
			self.remove(self)
