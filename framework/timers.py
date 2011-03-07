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

import time
import logging

log = logging.getLogger('pygab.timers')

class TimerFramework:
	def __init__(self):
		self.timers = NamedThreadPool()

	def process(self):
		"""processTimers() -> None

		Process any timers that have been set.
		Timers are deleted as they run out.
		This function can be replaced if needed.

		"""
		for thread in self.timers:
			try:
				next(thread)
			except StopIteration:
				self.timers.remove_by_obj(thread)


	def add(self, delay, callback, *args, repeat=-1, run_now=False):
		"""addTimer(delay, callback, *args, repeat=-1, run_now=False) -> None

		Add an event to run at a set interval.
		'args' are any extra arguments to be passed to the event.

		"""
		#if type.lower() == "hours":
		#	delay = delay * 60 * 60
		#elif type.lower() == "minutes":
		#	delay = delay * 60

		def timer():
			"""Run the event after a period of time has passed."""
			nonlocal delay, repeat, callback, args
			last_run = 1 if run_now else time.time()

			while True:
				if time.time() - last_run >= delay:
					callback(*args)
					last_run = time.time()
					if repeat == 0:
						break
					elif repeat > 0:
						repeat -= 1
				yield

		timer.__name__ = callback.__name__
		timer.__doc__ = callback.__doc__

		self.timers.append(timer)
		return timer

	def remove(self, timer_name):
		"""removeTimer(str timer_name) -> None

		Delete an event's timer instance.

		"""
		if isinstance(timer_name, str):
			self.timers.remove(timer_name)
		else:
			self.timers.remove_by_obj(timer_name)

class ThreadPool:
	"""Enhanced threads list as class

	Assigns priority by adding the thread into the stream priority number of times.

	threads = ThreadPool()
	threads.append(threadfunc)  # not generator object
	if threads.query(num) <<has some property>>:
	threads.remove(num)
	"""
	def __init__(self):
		# List of all active threads
		self.active_threads = []
		# Dictionary of all initiated threads
		self.thread_table = {}
		# Thread Obj -> ID map dictionary
		self.objid_map = {}
		self.threads = 0

	def __getitem__(self, threadID):
		return self.thread_table.get(threadID, [None])[1]

	def __iter__(self):
		"""Iterate over the active threads"""
		for thread in self.active_threads:
			yield thread

	def sort(self, list_):
		"""Place holder for anysorting subclasses want to do to the threads."""
		return list_

	def append(self, threadfunc, docstring=None, priority=1):
		# Argument is the generator func, not the gen object
		# Every threadfunc should contain a docstring
		docstring = docstring or threadfunc.__doc__
		self.objid_map[threadfunc] = self.threads
		self.thread_table[self.threads] = (
			docstring,
			threadfunc(),
			priority,
		)
		self.threads += 1
		self.active_threads = [t[1] for t in self.sort(self.thread_table.values())]
		return self.threads - 1	   # return the threadID

	def remove(self, threadID):
		try:
			thread_data = self.thread_table[threadID]
			del self.thread_table[threadID]
		except KeyError:
			return
		self.active_threads.remove(thread_data[1])

	def remove_by_obj(self, obj):
		self.remove(self.objid_map.get(obj))

	def query(self, threadID):
		"Information on thread, if it exists (otherwise None)"
		return self.thread_table.get(threadID, [None])[0]

class NamedThreadPool(ThreadPool):
	def append(self, threadfunc, docstring=None, priority=1):
		# Argument is the generator func, not the gen object
		# Every threadfunc should contain a docstring
		docstring = docstring or threadfunc.__doc__
		self.objid_map[threadfunc] = threadfunc.__name__
		self.thread_table[threadfunc.__name__] = (
			docstring,
			threadfunc(),
			priority,
		)
		self.active_threads = [t[1] for t in self.sort(self.thread_table.values())]

class PriorityThreadPool(ThreadPool):
	def __getitem__(self, threadID):
		try:
			thread_data = self.thread_table[threadID]
		except KeyError:
			return None

		return [thread_data[1]] * max(1,thread_data[2])

class OrderedThreadPool(ThreadPool):
	def sort(self, list_):
		list_.sort(lambda x,y: cmp(x[2], y[2]))
		return list_
