from common.pluginmount import PluginMount

__all__ = ['PluginInitializers' ,'CommandMount', 'HookMount']

class PluginInitializers:
	"""
	Stores Initalization classes which run when the plugin is loaded.

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
	__metaclass__ = PluginMount

	def __init__(self, parent):
		self.parent = parent
		self.plugins[self.name] = self


class CommandMount:
	"""
	Mount point for bot commands normal users can perform.

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
	__metaclass__ = PluginMount

	def __init__(self, parent):
		self.parent = parent

		# Initalize the plugin's thread
		self.init_thread()
		self.plugins[self.name] = self

	def init_thread(self):
		self._thread = self.thread()
		self._thread.send(None)

	def process(self, user, msg, whisper=False):
		try:
			self._thread.send((user, msg, whisper))
		except StopIteration:
			self.init_thread()
		except GeneratorExit:
			CommandMount.remove(self)

	@staticmethod
	def thread_base(fn):
		def thread(self):
			while 1:
				try: args = (yield)
				except GeneratorExit: raise

				if args is None: continue
				user, args, whisper = args
				fn(self, user, args, whisper)
		return thread

	def __exit__(self, *args):
		self._thread.close()
		CommandMount.remove(self)

class HookMount:
	"""
	Mount point for hooks into various processes.

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

	__metaclass__ = PluginMount

	def __init__(self, parent):
		self.parent = parent

		# Initalize the plugin's thread
		self.init_thread()
		self.plugins[self.name] = self

	def init_thread(self):
		self._thread = self.thread()
		self._thread.send(None)

	@staticmethod
	def sort(iter):
		"""Sort decending by each item's priority attribute."""
		iter.sort(lambda x,y: cmp(x.priority, y.priority), reverse=True)
		return iter

	def process(self, user, msg):
		try:
			self._thread.send((user, msg))
		except StopIteration:
			self.init_thread()
		except GeneratorExit:
			CommandMount.remove(self)

	@staticmethod
	def thread_base(fn):
		def thread(self):
			result = None
			while 1:
				try: args = (yield result)
				except GeneratorExit: raise

				if args is None:
					result = None
					continue
				user, args = args
				result = False

				result = fn(self, user, args)
		return thread


	def __exit__(self, *args):
		self._thread.close()
		HookMount.remove(self)
