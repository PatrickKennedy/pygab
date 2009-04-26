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

import traceback

from	common.dict4ini	import	DictIni
from	os.path			import	abspath, curdir, join

global iMan

class DictIniWrapper(DictIni):
	def has_entry(self, section, key, entry):
		"""has_entry(str section, str key, * entry) -> bool

		Return true if 'entry' is in the 'key' of 'section' of 'ini'

		"""
		if self.has_key(section) and self[section].has_key(key):
			return entry in self[section][key]
		return False

	def add_entry(self, section, key, entry):
		"""add_entry(str section, str key, * entry) -> bool

		Add 'entry' to 'key' in 'section'. Return False if entry exists.

		"""
		if self.has_entry(section, key, entry):
			return False

		if self.has_key(section) and self[section].has_key(key):
			self[section][key].append(entry)
		else:
			self[section][key] = [entry]
		self.save()
		return True

	def del_entry(self, section, key, entry):
		"""del_entry(str section, str key, * entry) -> bool

		"del an flag, return 0 if they didn't have the flag"

		"""
		if not self.has_entry(section, key, entry):
			return False

		self[section][key].remove(entry)
		if not self[section][key]:
			del self[section][key]
		self.save()
		return True

	def set_entry(self, section, key, entry):
		"""set_entry(str section, str key, * entry) -> bool

		Replace all entries in 'key' in 'section' with 'entry'

		"""
		self[section][key] = [entry]
		self.save()
		return True


class IniManager(object):

	"""IniManager is a convience class for managing ini files.

	It provides functions for loading and unloading ini files and
	for managing the files.

	"""

	def __init__(self, temp_path='templates'):
		"""IniManager(str temp_path='templates') -> None

		"""
		self.temp_path = (curdir, temp_path)
		# Keep track of the number of times an .ini is loaded/unloaded.
		self.__references = {}

	def __contains__(self, name):
		"""__contains__(str name) -> bool

		Return True if 'name'.ini is loaded.
		ex. 'roster' in iMan

		"""

		return hasattr(self, name)

	def __iter__(self):
		for name in self.__references.iterkeys():
			yield self[name]

	def __getitem__(self, name):
		return getattr(self, name)

	def __setitem__(self, name, value):
		setattr(self, name, value)

	def __delitem__(self, name):
		return delattr(self, name)

	def load(self, name, *subfolders):
		"""load_ini(str name, *subfolders) -> Bool

		Loads 'name'.ini making it available for use.
		Return True if 'name'.ini loaded properly.

		"""
		if self.loaded(name):
			return True
		name = name.lower()
		path = [curdir]
		path.extend(subfolders)
		path.append("%s.ini" % name)
		try:
			ini = DictIniWrapper(join(*path), encoding = "utf8")
			self[name] = ini
			ini.read()
			self.__references[name] = self.__references.get(name, 0) + 1
			return True
		except IOError:
			return False
		except:
			traceback.print_exc()
			return False

	def loaded(self, name):
		"""loaded(str name) -> bool

		Return True if 'name'.ini is loaded.

		"""
		return name in self

	def unload(self, name, save=False):
		"""unload(str name, bool save=False) -> bool

		Unloads 'name'.ini.
		If 'save' is true ini.save will be called.

		"""
		name = name.lower()
		if name in self:
			self.__references[name] = self.__references.get(name, 0) - 1
			if self.__references[name] >= 0:
				if save:
					self[name].save()
				del self[name]
				del self.__references[name]
				return True
		return False

	def rename(self, name, new_name):
		"""rename(str name, str new_name) -> None

		Renames the ini 'name' to 'new_name'.

		"""
		name = name.lower()
		ini = self[name]
		self[new_name] = ini
		ini.setfilename(new_name)
		ini.save()

	def readall(self):
		"""readall() -> None

		Read all loaded ini files.

		"""
		for ini in self:
			ini.read()

	def saveall(self):
		"""readall() -> None

		Save all loaded ini files.

		"""
		for ini in self:
			ini.save()
			#print "DEBUG: Saving %s" % ini.getfilename()

		#print "Debug: IniManager has saved all ini files."

	def has_entry(self, ini, section, key, entry):
		"""has_entry(* ini, str section, str key, * entry) -> bool

		Return true if 'entry' is in the 'key' of 'section' of 'ini'

		"""
		if not isinstance(ini, DictIni):
			# Always returns False if the ini hasn't been loaded.
			try:
				ini = self[ini]
			except KeyError:
				return False

		if ini.has_key(section) and ini[section].has_key(key):
			return entry in ini[section][key]
		return False

	def add_entry(self, ini, section, key, entry):
		"""add_entry(* ini, str section, str key, * entry) -> bool

		Add 'entry' to 'key' in 'section'. Return False if entry exists.

		"""
		if not isinstance(ini, DictIni):
			# Always returns False if the ini hasn't been loaded.
			try:
				ini = self[ini]
			except KeyError:
				return False

		if self.has_entry(ini, section, key, entry):
			return False

		if ini.has_key(section) and ini[section].has_key(key):
			ini[section][key].append(entry)
		else:
			ini[section][key] = [entry]
		ini.save()
		return True

	def del_entry(self, ini, section, key, entry):
		"""del_entry(* ini, str section, str key, * entry) -> bool

		"del an flag, return 0 if they didn't have the flag"

		"""
		if not isinstance(ini, DictIni):
			# Always returns False if the ini hasn't been loaded.
			try:
				ini = self[ini]
			except KeyError:
				return False

		if not self.has_entry(ini, section, key, entry):
			return False

		ini[section][key].remove(entry)
		if not ini[section][key]:
			del ini[section][key]
		ini.save()
		return True

	def set_entry(self, ini, section, key, entry):
		"""set_entry(* ini, str section, str key, * entry) -> bool

		Replace all entries in 'key' in 'section' with 'entry'

		"""
		if not isinstance(ini, DictIni):
			# Always returns False if the ini hasn't been loaded.
			try:
				ini = self[ini]
			except KeyError:
				return False

		ini[section][key] = [entry]
		ini.save()
		return True

	def _merge_template(self, ini, template):
		"""_merge_template(DictIni ini, DictIni template) -> DictIni

		Fills in any missing entries from the config.
		Note: You can pass any dictionary style object through this.

		"""
		if not isinstance(ini, DictIni):
			ini = self[ini]

		for (section, key) in template.items():
			if not ini.has_key(section) or not ini[section].has_key(key):
				self._read_or_prompt(ini, section, key, template.get_comment(key))
				ini[section][key] = template[section][key]
		return ini

	def _read_or_prompt(self, ini, section, option, description):
		"""Read an option from 'ini', or prompt for it"""
		if not ini[section].get(option):
			ini[section][option] = raw_input('%s\nLeave Blank to use Default > ' % description)

iMan = IniManager()
