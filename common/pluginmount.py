class PluginMount(type):
	def __init__(cls, name, bases, attrs):
		if not hasattr(cls, 'plugins'):
			# This branch only executes when processing the mount point itself.
			# So, since this is a new plugin type, not an implementation, this
			# class shouldn't be registered as a plugin. Instead, it sets up a
			# list where plugins can be registered later.
			cls.plugins = {}
		else:
			# This must be a plugin implementation, which should be registered.
			# Simply appending it to the list is all that's needed to keep
			# track of it later.
			cls.plugins[cls.name] = cls

	def get_plugin_list(self, **attrs):
		'''get_plugin_list(str **attr) -> list

		Return a list of plugins stored in a mount.
		If attr is not empty it will return a list of plugins with matching
		attributes. If a value passed is "True" it will accept any plugins that
		have that attribute defined.

		'''

		if not attrs:
			return [p for p in self.plugins]

		plugins = []
		for p in self.plugins:
			# flag is set to False if an attribute doesn't match.
			flag = True
			for attr, value in attrs.items():
				if value == True:
					if not hasattr(p, attr):
						flag = False
				else:
					if getattr(p, attr, None) != value:
						flag = False
						break
			if flag:
				plugins.append(p)
		return plugins


	def append(self, cls):
		self.plugins[cls.name] = cls

	def remove(self, cls):
		del self.plugins[cls.name]
