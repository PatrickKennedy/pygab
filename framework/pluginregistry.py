class PluginRegistry(type):
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
			cls.append(cls)

	@staticmethod
	def sort(iter):
		return iter

	def get_plugin_list(self, **attrs):
		'''get_plugin_list(str **attr) -> list

		Return a list of plugins stored in a mount.
		If attr is not empty it will return a list of plugins with matching
		attributes. If a value passed is "True" it will accept any plugins that
		have that attribute defined.

		'''

		if not attrs:
			for p in self.sort(self.plugins.values()):
				yield p

		plugins = []
		for p in self.sort(self.plugins.values()):
			# flag is set to False if an attribute doesn't match.
			flag = True
			for attr, value in attrs.items():
				# Unless we're looking to see if the attribute isn't there
				# all instances of a missing attribute imediately fail the
				# plugin.
				if not hasattr(p, attr):
					if value is not False:
						continue

				# If we're just looking to see if the attribute is defined
				# then this imediately succeeds.
				if value is True:
					continue

				attr_value = getattr(p, attr, [])
				# If the passed value is an iterator then attempting an 'in'
				# check would yeild nasty errors.
				if not hasattr(value, '__iter__') and hasattr(attr_value, '__contains__'):
					if value not in attr_value:
						flag = False
						break

				# At the end of the day we may just want to check for equality
				elif value != attr_value:
					flag = False
					break

			if flag:
				yield p

	def append(self, cls):
		if cls.name in self.plugins:
			print "WARNING: The Plugin Class %s Has been Overwritten" % cls.name
		self.plugins[cls.name] = cls

	def remove(self, cls):
		del self.plugins[cls.name]
