import sgmllib
import urllib
import random
import re

import	const
import	utils

module = utils.get_module()
exec(utils.get_import(mod=module, from_=['utils']))
try:
	exec(utils.get_import(mod=module, from_=['mounts'],
		import_=['HookMount', 'CommandMount']))
except ImportError, e:
	print e

class UrlParser(sgmllib.SGMLParser):
	"A simple parser class."

	def parse(self, s):
		"Parse the given string 's'."
		self.feed(s)
		self.close()

	def __init__(self, verbose=0):
		"Initialise an object, passing 'verbose' to the superclass."

		sgmllib.SGMLParser.__init__(self, verbose)
		self.hyperlinks = []
		self.descriptions = []

	def start_a(self, attributes):
		"Process a hyperlink and its 'attributes'."

		for name, value in attributes:
			if name == "href" and value[1:].isdigit():
				self.hyperlinks.append(value)

	def get_hyperlinks(self):
		"Return the list of hyperlinks."

		return self.hyperlinks


class QuoteParser(sgmllib.SGMLParser):
	"A simple parser class."

	def parse(self, s):
		"Parse the given string 's'."
		self.feed(s)
		self.close()

	def __init__(self, verbose=0):
		"Initialise an object, passing 'verbose' to the superclass."

		sgmllib.SGMLParser.__init__(self, verbose)
		self.quote = ''
		self.inside_quote = 0
		self.starting_quote = 0

	def start_a(self, attributes):
		"Process a hyperlink and its 'attributes'."

		for name, value in attributes:
			if name == "href" and value[1:].isdigit():
				self.quote = "Bash.org Quote # %s\n" % value[1:]


	def start_p(self, attributes):
		"Process a hyperlink and its 'attributes'."

		for name, value in attributes:
			if name == "class" and value == "qt":
				self.inside_quote = 1

	def end_p(self):
		"Record the end of a hyperlink."

		self.inside_quote = 0

	def handle_data(self, data):
		"Add any part of the page between the <p> tag."
		if self.inside_quote:
			self.quote += data

	def get_quote(self):
		"Return the list of hyperlinks."

		return self.quote

class Bash(CommandMount):
	name = 'bash'
	rank = const.RANK_USER
	file = __file__

	filter = re.compile("(?i)(jerk(ked|ed)(\soff)*|shit|fuc*ke*r*|ass|sex|mast[ur]bat(e|ion)|penis|bitch|dick)")
	urlparser = UrlParser()
	quoteparser = QuoteParser()
	
	@CommandMount.thread_base
	def thread(self, user, quote, whisper):
		"""Get a random quote.
	Usage: )bash [<number>]
	Note: Some lag time is normal."""
		if quote:
			quote = quote.strip('?')

			if not quote.isdigit():
				self.parent.error(user, cmd_bash.__doc__)
				return

			f = urllib.urlopen('http://bash.org/?%s' % quote)
			s = f.read()
			self.quoteparser.parse(s)
			quote = self.quoteparser.get_quote()
			if not quote:
				self.parent.error(user, "That quote doesn't seem to exist.")
				return
		else:
			f = urllib.urlopen("http://bash.org/?random")
			s = f.read()
			f.close()

			self.urlparser.parse(s)

			links = self.urlparser.get_hyperlinks()
			list_length = len(links)
			for i in range(list_length):
				f = urllib.urlopen('http://bash.org/%s' % random.choice(links))
				s = f.read()
				f.close()
				self.quoteparser.parse(s)
				quote = self.quoteparser.get_quote()
				if not self.filter.search(quote):
					break
		self.parent.sendtoall(quote)
