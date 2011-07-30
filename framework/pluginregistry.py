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

class Registry(type):
	"""The quintessential class registry."""
	def __init__(cls, name, bases, attrs):
		if not hasattr(cls, 'plugins'):
			# This branch only executes when processing the mount point itself.
			# So, since this is a new plugin type, not an implementation, this
			# class shouldn't be registered as a plugin. Instead, it sets up a
			# list where plugins can be registered later.
			cls.plugins = cls.container()
		else:
			# This must be a plugin implementation, which should be registered.
			# Simply appending it to the list is all that's needed to keep
			# track of it later.
			cls.append(cls)

	@staticmethod
	def container():
		"Return a registry specific type of container"
		return []

	def append(self, cls):
		"Handle registry specific append needs"
		self.plugins.append(cls)

class LocationRegistry(Registry):
	"""Simple registry for Location classes"""
	# This is just a convenience method so we can use:
	# `Locations.EvMsg`
	# instead of:
	# `Locations.plguins.get("EvMsg")
	def __getattr__(self, attr):
		if attr == "plugins":
			if 'plugins' in self.__dict__:
				return self.__dict__['plugins']
			else:
				raise AttributeError
		a = self.plugins.get(attr, None)
		#if a is None:
		#	a = super(LocationRegistry, self).__getattr__(attr)
		return a

	def __dir__(self):
		return self.plugins.keys()

	def __iter__(self):
		return iter(self.plugins.values())

	@staticmethod
	def container(): return {}
	def append(self, cls): self.plugins[cls.__name__] = cls

	def remove(self, cls): del self.plugins[cls.__name__]
