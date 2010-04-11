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

## PLEASE NOTE
## utils.py performs a * import on the current module's custom utils.py file
## This allows plugins to function seemlessly across modules.

from __future__ import with_statement

import	datetime
import	errno
import	os
import	re
import	sys
import	time
import	traceback

from 	common.ini		import iMan
from	xmpp.protocol	import JID

#Command exception classes
class CommandHelp(Exception):pass
class CommandError(Exception):pass

def get_module():
	'''get_module() -> str

	Return the name of the module by importing __main__
	Warning: If this is called on import in a module that is imported
				by __main__ it will cause an infinate import loop.

	'''
	# These two lines are depricated lines.
	# It turns out __main__.__file__ == sys.argv[0] so using sys.argv[0]
	# removes the risk of infinate import loops! =]
	#import __main__
	#selffile = os.path.split(__main__.__file__)[1]
	selffile = os.path.split(sys.argv[0])[1]
	return os.path.splitext(selffile)[0]

def get_import(mod=get_module(), from_=[], import_=[]):
	'''get_import(mod=get_module(), from_=[], import_=[]) -> str

	Return a string that can be used to import from the running module.
	mod		- The name of the module or base python module.
	from_   - A list of sub-modules. Joined by '.'s
	import_ - A list of objects to import from a module. Join by ','s

	Warning: If this is called on import in a module that is imported
				by __main__ it will cause an infinate import loop.

	'''
	f = ''
	i = '*'

	if from_:
		assert isinstance(from_, list)
		f = '.%s' % '.'.join(from_)

	if import_:
		assert isinstance(import_, list)
		i = ', '.join(import_)

	if from_:
		return 'from %s%s import %s' % (mod, f, i)

#=============================
#=         User Tools        =
#=============================
#======
#= User Names
def getname(jid):
	"""getname(xmpp.protocol.JID jid) -> unicode

	Converts a user@domain/resource to simply a user name.

	"""
	# Make sure all JIDs are stardized to be JID objects.
	# They're much easier to manipulate.
	assert isinstance(jid, JID)
	domain = iMan.config.server.domain
	if jid.domain == domain:
		return unicode(jid.node)

	if '%' in jid.node and jid.domain != domain:
		return unicode(jid.node[:jid.node.find('%')])

	return unicode(jid)

def getnickname(jid):
	"""getnickname(xmpp.protocol.JID jid) -> unicode

	Converts a user@domain/resource a possibly user-defined nickname.

	"""
	# Make sure all JIDs are stardized to be JID objects.
	# They're much easier to manipulate.
	assert isinstance(jid, JID)

	if has_nick(jid):
		return get_nick(jid)

	# If there is no nickname, return the name of the user.
	return getname(jid)

def getjid(user, domain='', resource=''):
	"""getjid(str user, str domain=iMan.config.server.domain
		str resource=iMan.config.server.resource) -> xmpp.protocol.JID

	Returns a JID for 'user'.

	"""
	if isinstance(user, JID):
			return user

	if not domain:
		domain = iMan.config.server.domain

	# We can't do anything with non-strings.
	assert isinstance(user, basestring), 'getjid got passed a %s' % type(user)

	if '@' in user:
		user = user.split('@', 1)[0]
	return JID(
		node=user,
		domain=domain,
		resource=resource
	)

def has_nick(jid):
	"""Returns True if jid has a nickname"""
	pass

def get_nick(jid):
	"""Returns the nickname of jid"""
	pass

def has_attr(jid, attr, value):
	"""Return True if 'jid' has value."""
	return iMan.has_entry('roster', jid, attr, value)
def del_attr(jid, attr, rank):
	"""Delete value from 'jid'."""
	return iMan.del_entry('roster', jid, attr, value)
def add_attr(jid, attr, rank):
	"""Add value to 'jid'."""
	return iMan.add_entry('roster', jid, attr, value)
def set_attr(jid, attr, rank):
	"""Set 'jid's attr to value."""
	return iMan.set_entry('roster', jid, attr, value)

def isbanned(user):
	if False and iMan.loaded('roster'):
		return 'banned' in iMan.config[getname(user).lower()].rank
	return getname(user).lower() in iMan.config.users.banned

def ismod(user):
	if False and iMan.loaded('roster'):
		return 'mod' in iMan.config[getname(user).lower()].rank
	return getname(user).lower() in iMan.config.users.mod

def isadmin(user):
	if False and iMan.loaded('roster'):
		return 'admin' in iMan.config[getname(user).lower()].rank
	return getname(user).lower() in iMan.config.users.admin


#=====
#= Misc (Ordered Alphabetically)
def addUser(jid):
	jid = unicode(jid.getStripped())
	iMan.set_entry('roster', jid, "last_login", time.time())
	iMan.set_entry('roster', jid, "last_message", time.time())
	set_attr(jid, 'rank', const.RANK_USER)

def formattime(time_tuple, format=''):
	"""formattime(tuple time, str format=iMan.config.system.timeformat) -> str

	Convienience function for time.strftime().

	"""
	if not format:
		format = iMan.config.system.get('timeformat', '')

	return time.strftime(format, time_tuple)

# Get the target of a command.
# By passing a string with a space you can give
# a reason for targeting the person.
def split_target(target):
	"""split_target(str target) -> list

	Return the target of a command and a reason if there is a space in 'target'

	"""
	reason = ''

	if ' ' in target:
		target, reason = target.split(' ', 1)

	return [getjid(target), reason]


def is_plugin(args):
	return args in iMan.config.system.plugins

def isuser(bot, user):
	"Return True if the user exists in the bot."
	user = getjid(user)
	try:
		return bot.getJidStatus(user).items() != None
	except:
		return False

def isonline(bot, user):
	"Return true if the user is online."
	user = getjid(user)
	try:
		return bool(bot.getJidStatus(user).items())
	except:
		return False

def isactive(bot, jid):
	if not isonline(bot, jid):
		return False

	jid_status = bot.getJidStatus(jid)
	if jid_status[jid][0] in ["online", "chat"]:
		return True

def isaway(bot, jid):
	if not isonline(bot, jid):
		return True

	jid_status = bot.getJidStatus(jid)
	if jid_status[jid][0] in ["away", "dnd", "xa"]:
		return True


	iMan.load('roster')
	user = jid.getStripped()
	try:
		return 'afk' in iMan.roster[user]
	finally:
		iMan.unload('roster')



#=====================================
#=         Chat Filter Tools         =
#=====================================
def convert_seq(seq, y = None):
#======================
#= y = 1 sets the string up for the langauge filter.
#= y = 2 sets the string up to be listed in /wordfilter.
	j = None
	for i in seq:
		k = i
		if y == 1:
			k = re.sub('\[*\B\W*\]*','\W*',k)
			k = re.sub('\[(([^\]])\\\W\*([^\]]))+\]','\W*[\g<2>\g<3>]\W*',k)
			k = re.sub('\((([^\|]+)\|*([^\)]+))\)','\W*(\g<2>|\g<3>)\W*',k)
			k = re.sub('(?<!W)\*','*\W*',k)
			k = re.sub('u""','',k)
		elif y == 2:
			k = re.sub('\Z\W*','\n',k)
		if j:
			j += ' ' + k
		else:
			j = k
		#print j
	return j

def cuss_list():
	"Returns a formated Regex"
	iMan.core.read()
	j = convert_seq(iMan.core.optional.get("wordfilter"), y = 1)
	j = j.strip()
	j = re.sub('\s','|',j)
	#j = '(?i)(?!\\B)(' + j + ')+(\\b|\\B)'
	#Alternate, more precice way, but consumes more CPU time.
	j = '(?i)(?!\\B)(?:(?:[^aeiou](?=[^aeiou]))|(?:[aeiou](?=[aeiou])))?(' + j + ')+(?=\\b)'
	return j

def clean_string(string):
	'Returns a filtered string.'
	return re.sub(cuss_list(), iMan.core.optional.filtermask, string)

#========================
#=         Misc         =
#========================
def sortdict(dict, item="key"):
	"Returns an alphabetical list of keys, values, or both,"
	if item.startswith('key'):
		return dict.keys().sort()
	if item.startswith('value'):
		return dict.values().sort()
	return [t.sort() for t in dict.items()]

def confirmdir(path):
	if not os.path.isdir(path):
		os.mkdir(path)
		print "ALERT: A directory doesn't exist, making folder \"%s\"" % path
	return

def open_if_exists(filename, mode='r'):
	"""open_if_exists(filename: str, mode='r': str)
	Return an open file object for the filename if the file exists,
	otherwise `None`.
	"""
	try:
		return file(filename, mode)
	except IOError, e:
		if e.errno not in (errno.ENOENT, errno.EISDIR):
			raise

def pluralize(i, plural_form='s'):
	"""Return 'plural_form' if i != 1"""
	return (i != 1 and plural_form or '')

def date_diff(then):
	"""date_diff(then: datetime.datetime) -> str

	Build a date string that changes as time goes on.
	Examples:
		Item posted
		< 5 seconds: a moment ago
		< 1 minute: 16 seconds ago
		< 1 hour: 34 minutes ago
		today: Today, 09:23
		this week: Tuesday, 11:40
		later: May 13 08

	"""

	assert isinstance(then, datetime.datetime), "recieved %s instead of %s" % \
												(type(then), datetime.datetime)

	diff = (datetime.datetime.now() - then)
	seconds = diff.seconds
	minutes = seconds / 60
	hours = minutes / 60
	days = diff.days

	if days > 7:
		return then.strftime('%b %d, %Y, %H:%M GMT')
	if days < 1:
		if seconds < 5:
			return 'a moment ago'
		if seconds < 60:
			return '%d second%s ago' % (seconds, pluralize(seconds))
		if minutes < 60:
			return '%d minute%s ago' % (minutes, pluralize(minutes))

		return then.strftime('Today, %H:%M GMT')

	return then.strftime('%A, %H:%M GMT')

def time_since(then, suffix=' ago', depth=2):
	"""Return a human readable difference between two datetimes.

	Arguemnts:
	then - datetime object representning a time before now.
	suffix - A string to be appended to the returned string.
	depth - How many levels of time to traverse and display beginning form days.

	"""
	diff = (datetime.datetime.now() - then)
	# Each of the levels uses modulus to get the relative amount of time.
	# Other wise we end up with things like '1 hour, 80 minutes and 4857 seconds ago'
	levels = [
		(diff.days, '%d day%s'),
		(((diff.seconds // 60) // 60) % 24, '%d hour%s'),
		((diff.seconds // 60) % 60, '%d minute%s'),
		(diff.seconds % 60, '%d second%s')
	]
	time_list = []
	time_str = ''

	for level, descriptor in levels:
		if not level:
			continue
		time_list.append(descriptor % (level, pluralize(level)))
		depth -= 1
		if depth <= 0:
			break

	# If there are multiple times we need to throw "and" into the sentence.
	if len(time_list) > 1:
		time_str = ', '.join(time_list[:-1]) +', and '+ time_list[-1]
	else:
		time_str = time_list[0]

	return time_str + suffix

def get_svn_revision():
	"""get_svn_revision() -> str

	Return the HEAD SVN Revition number of the module.

	"""
	module = get_module()
	entry_path = os.path.join('.', module, '.svn', 'entries')
	if os.path.isdir(os.path.join('.', module, '.svn')) and os.path.getsize(entry_path):
		with open(entry_path, 'r') as f:
			for i in xrange(4):
				revision = f.readline().rstrip('\n')

		if not revision.isdigit():
			revision = 'Unknown'

		iMan.config.system.revision = revision

		return revision

	return iMan.config.system.get('revision', 'Unknown')


def debug(tag, msg):
	"Sends a debug message to the console"
	try:
		tags = iMan.config.system.get("debugtag", [])
		if tag in tags or 'all' in tags:
			print "DEBUG:",msg
	except:
		print "DEBUG:",msg
