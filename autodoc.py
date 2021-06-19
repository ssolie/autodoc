#!/usr/bin/python
#
# This script parses source code files and outputs Amiga-style autodocs.
# It is designed to be identical to the original Autodoc tool in functionality
# but not all of the original Autodoc tool features are implemented.
#
# Special thanks to https://regex101.com/ for the assistance.
#
# Compatible with Python 2.5 and higher.
# 
#
# autodoc.py - Generates Amiga-style autodocs from source code
# Copyright (C) 2021 Steven Solie
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>

import sys
import re
import getopt

# Embedded version string.
verstag = '$VER: autodoc.py 54.2 (18.6.2021)'

# All output goes to outfile.
#
# In future, this can be set to other files.
outfile = sys.stdout

# Default command line arguments.
args = {
	'i': False,
	'o': False,
	'u': False,
	'l': 78,
	'c': False,
	'f': False,
	'I': False,
	'infile': []
}

def print_usage():
	print("Usage: autodoc.py [option] file...")
	print("-i    : Process only INTERNAL (i) autodocs")
	print("-o    : Process only OBSOLETE (o) autodocs")
	print("-u    : Process FUTURE (f) autodocs")
	print("-lnum : Set line length to num (default 78)")
	print("-c    : Do not convert \\* to /* and *\\ to */")
	print("-f    : No form feeds between entries")
	print("-I    : Do not output table of contents before entries")
	print("file  : One or more input files")

def parse_args():
	""" Parse command line arguments
	Returns True if successful or False on error.
	"""
	try:
		opts, files = getopt.getopt(sys.argv[1:], "ioul:cfI")
	except getopt.GetoptError:
		return False

	for opt, val in opts:
		if opt == '-i':
			args['i'] = True

		if opt == '-o':
			args['o'] = True

		if opt == '-u':
			args['u'] = True

		if opt == '-l':
			args['l'] = int(val)

		if opt == '-c':
			args['c'] = True

		if opt == '-f':
			args['f'] = True

		if opt == '-I':
			args['I'] = True

	if (len(files)) == 0:
		return False
	else:
		args['infile'] = files

	return True


def print_form_feed():
	""" Outputs optional form feed character """
	if not args['f']:
		outfile.write( chr(0x0C) )


class autodoc:
	""" Autodoc class used to contain a single complete autodoc.
	"""
	def __init__(self, name, body):
		""" Construct with autodoc name and body.
		"""
		self.name = name
		self.body = body

	def __lt__(self, other):
		""" Less than operator for sorting by name.
		"""
		return self.name.lower() < other.name.lower()

	def write_toc_entry(self):
		""" Write the table of contents entry only.
		"""
		outfile.write(self.name + "\n")

	def write(self):
		""" Write out the entire autodoc including name and body.
		"""
		width = args['l']  # line width as specified by the user

		outfile.write(self.name + "\n")

		lines = self.body.split('\n')
		for line in lines[:-1]:
			if len(line) < width:
				outfile.write(line)
			else:
				# We only handle 2 lines worth of splitting as did the
				# original autodoc tool.
				outfile.write(line[:width - 1] + '\n')
				outfile.write(line[width - 1:])

			outfile.write('\n')

		# The last line should not have a line feed appended.
		outfile.write(lines[-1])

		print_form_feed()


class autodoclist:
	""" Contains a list of autodocs.
	"""
	def __init__(self):
		""" Constructor sets up for parsing.
		"""
		# Regex for finding autodoc block header
		self.head_regex = re.compile(r"""^/\*\s?\*{3,}(.)\* (\S*) \**""", re.MULTILINE)

		# Regex for finding autodoc body contents
		self.body_regex = re.compile(r"""^\*{1,}(.*$\n)""", re.MULTILINE)

		# Regex for finding autodoc block trailer
		self.tail_regex = re.compile(r"""^\*{3,}""", re.MULTILINE)

		# Where to store the list of autodoc objects.
		self.autodocs = []

	def parse_file(self, filename):
		""" Parses the filename and adds any autodocs to the list.
		"""
		inside_autodoc = False
		name = None

		# The content of the file is manipulated as we parse.
		#
		# First we search for the header. When found, we split
		# the remainder of the file into lines and parse those.
		file = open(filename)
		content = file.read()
		file.close()

		while True:
			if not inside_autodoc:
				head_match = self.head_regex.search(content)
				if head_match:
					type = head_match.group(1)
					name = head_match.group(2)

					# Move content past the head.
					head_span = head_match.span()
					content = content[head_span[1]:]

					# Exclusion filters
					if args['i'] and type != 'i':
						continue

					if args['o'] and type != 'o':
						continue

					# Inclusion filters
					if args['i'] and type == 'i':
						inside_autodoc = True

					if args['o'] and type == 'o':
						inside_autodoc = True

					if args['u'] and type == 'f':
						inside_autodoc = True

					if type == '*':
						inside_autodoc = True
				else:
					# No more autodoc headers in the file.
					break
			else:
				body = ""
				lines = content.splitlines(True)
				for line in lines:
					tail_match = self.tail_regex.match(line)
					if tail_match:
						doc = autodoc(name, body)
						self.autodocs.append(doc)

						# Go back to searching for a header.
						inside_autodoc = False
						break
					else:
						body_match = self.body_regex.match(line)
						if body_match:
							body_string = body_match.group(1)

							# Do optional string replacements.
							if not args['c']:
								body_string = body_string.replace("\\*", "/*")
								body_string = body_string.replace("*\\", "*/")

							body += body_string

	def sort(self):
		""" Sorts the list of autodocs.
		"""
		self.autodocs.sort()

	def write_toc(self):
		""" Writes the table of contents.
		"""
		outfile.write("TABLE OF CONTENTS\n\n")
		for doc in self.autodocs:
			doc.write_toc_entry()

		outfile.write("\n\n")
		print_form_feed()

	def write_autodocs(self):
		""" Writes all the parsed autodocs.
		"""
		for doc in self.autodocs:
			doc.write()


if __name__ == "__main__":
	if not parse_args():
		print_usage()
		exit(1)

	list = autodoclist()
	for file in args['infile']:
		list.parse_file(file)

	list.sort()

	if not args['I']:
		list.write_toc()

	list.write_autodocs()
