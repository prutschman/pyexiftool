# -*- coding: utf-8 -*-
# PyExifTool <http://github.com/smarnach/pyexiftool>
# Copyright 2021 Kevin M (sylikc)

# More contributors in the CHANGELOG for the pull requests

# This file is part of PyExifTool.
#
# PyExifTool is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the licence, or
# (at your option) any later version, or the BSD licence.
#
# PyExifTool is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See COPYING.GPL or COPYING.BSD for more details.

"""

This contains a helper class, which makes it easier to use the low-level ExifTool class

"""


from .exiftool import ExifTool

try:        # Py3k compatibility
	basestring
except NameError:
	basestring = (bytes, str)


# ======================================================================================================================

#def atexit_handler

# constants related to keywords manipulations
KW_TAGNAME = "IPTC:Keywords"
KW_REPLACE, KW_ADD, KW_REMOVE = range(3)


# ======================================================================================================================

class ExifToolHelper(ExifTool):
	""" this class extends the low-level class with 'wrapper'/'helper' functionality
	It keeps low-level functionality with the base class but adds helper functions on top of it
	"""
	
	# ----------------------------------------------------------------------------------------------------------------------
	def __init__(self, executable=None, common_args=None, win_shell=True, return_tuple=False):
		# call parent's constructor
		super().__init__(executable=executable, common_args=common_args, win_shell=win_shell, return_tuple=return_tuple)



	# ----------------------------------------------------------------------------------------------------------------------
	#def metadata_json(self, filenames):
	#	pass

	# ----------------------------------------------------------------------------------------------------------------------
	# i'm not sure if the verification works, but related to pull request (#11)
	def execute_json_wrapper(self, filenames, params=None, retry_on_error=True):
		# make sure the argument is a list and not a single string
		# which would lead to strange errors
		if isinstance(filenames, basestring):
			raise TypeError("The argument 'filenames' must be an iterable of strings")

		execute_params = []

		if params:
			execute_params.extend(params)
		execute_params.extend(filenames)

		result = self.execute_json(execute_params)

		if result:
			try:
				ExifToolHelper._check_sanity_of_result(filenames, result)
			except (IOError, error):
				# Restart the exiftool child process in these cases since something is going wrong
				self.terminate()
				self.run()

				if retry_on_error:
					result = self.execute_json_filenames(filenames, params, retry_on_error=False)
				else:
					raise error
		else:
			# Reasons for exiftool to provide an empty result, could be e.g. file not found, etc.
			# What should we do in these cases? We don't have any information what went wrong, therefore
			# we just return empty dictionaries.
			result = [{} for _ in filenames]

		return result

	# ----------------------------------------------------------------------------------------------------------------------
	# allows adding additional checks (#11)
	def get_metadata_batch_wrapper(self, filenames, params=None):
		return self.execute_json_wrapper(filenames=filenames, params=params)

	# ----------------------------------------------------------------------------------------------------------------------
	def get_metadata(self, in_param):
		"""Return all meta-data for the given files.
		
			This will ALWAYS return a list
			
			in_param can be a list(strings) or a string.
			
			wildcard strings are accepted as it's passed straight to exiftool

		The return value will have the format described in the
		documentation of :py:meth:`execute_json()`.
		"""
		if isinstance(in_param, basestring):
			return self.execute_json(in_param)
		elif isinstance(in_param, list):
			return self.execute_json(*in_param)
		else:
			raise TypeError("get_metadata only accepts a str/bytes or a list")

	# ----------------------------------------------------------------------------------------------------------------------
	# (#11)
	def get_metadata_wrapper(self, filename, params=None):
		return self.execute_json_wrapper(filenames=[filename], params=params)[0]

	# ----------------------------------------------------------------------------------------------------------------------
	# (#11)
	def get_tags_batch_wrapper(self, tags, filenames, params=None):
		params = (params if params else []) + ["-" + t for t in tags]
		return self.execute_json_wrapper(filenames=filenames, params=params)

	# ----------------------------------------------------------------------------------------------------------------------
	def get_tags_batch(self, tags, filenames):
		"""Return only specified tags for the given files.

		The first argument is an iterable of tags.  The tag names may
		include group names, as usual in the format <group>:<tag>.

		The second argument is an iterable of file names.

		The format of the return value is the same as for
		:py:meth:`execute_json()`.
		"""
		# Explicitly ruling out strings here because passing in a
		# string would lead to strange and hard-to-find errors
		if isinstance(tags, basestring):
			raise TypeError("The argument 'tags' must be "
							"an iterable of strings")
		if isinstance(filenames, basestring):
			raise TypeError("The argument 'filenames' must be "
							"an iterable of strings")
		params = ["-" + t for t in tags]
		params.extend(filenames)
		return self.execute_json(*params)

	# ----------------------------------------------------------------------------------------------------------------------
	# (#11)
	def get_tags_wrapper(self, tags, filename, params=None):
		return self.get_tags_batch_wrapper(tags, [filename], params=params)[0]

	# ----------------------------------------------------------------------------------------------------------------------
	def get_tags(self, tags, filename):
		"""Return only specified tags for a single file.

		The returned dictionary has the format described in the
		documentation of :py:meth:`execute_json()`.
		"""
		return self.get_tags_batch(tags, [filename])[0]

	# ----------------------------------------------------------------------------------------------------------------------
	# (#11)
	def get_tag_batch_wrapper(self, tag, filenames, params=None):
		data = self.get_tags_batch_wrapper([tag], filenames, params=params)
		result = []
		for d in data:
			d.pop("SourceFile")
			result.append(next(iter(d.values()), None))
		return result


	# ----------------------------------------------------------------------------------------------------------------------
	def get_tag_batch(self, tag, filenames):
		"""Extract a single tag from the given files.

		The first argument is a single tag name, as usual in the
		format <group>:<tag>.

		The second argument is an iterable of file names.

		The return value is a list of tag values or ``None`` for
		non-existent tags, in the same order as ``filenames``.
		"""
		data = self.get_tags_batch([tag], filenames)
		result = []
		for d in data:
			d.pop("SourceFile")
			result.append(next(iter(d.values()), None))
		return result

	# ----------------------------------------------------------------------------------------------------------------------
	# (#11)
	def get_tag_wrapper(self, tag, filename, params=None):
		return self.get_tag_batch_wrapper(tag, [filename], params=params)[0]

	# ----------------------------------------------------------------------------------------------------------------------
	def get_tag(self, tag, filename):
		"""Extract a single tag from a single file.

		The return value is the value of the specified tag, or
		``None`` if this tag was not found in the file.
		"""
		return self.get_tag_batch(tag, [filename])[0]

	# ----------------------------------------------------------------------------------------------------------------------
	def copy_tags(self, fromFilename, toFilename):
		"""Copy all tags from one file to another."""
		self.execute("-overwrite_original", "-TagsFromFile", fromFilename, toFilename)


	# ----------------------------------------------------------------------------------------------------------------------
	def set_tags_batch(self, tags, filenames):
		"""Writes the values of the specified tags for the given files.

		The first argument is a dictionary of tags and values.  The tag names may
		include group names, as usual in the format <group>:<tag>.

		The second argument is an iterable of file names.

		The format of the return value is the same as for
		:py:meth:`execute()`.

		It can be passed into `check_ok()` and `format_error()`.
		"""
		# Explicitly ruling out strings here because passing in a
		# string would lead to strange and hard-to-find errors
		if isinstance(tags, basestring):
			raise TypeError("The argument 'tags' must be dictionary "
							"of strings")
		if isinstance(filenames, basestring):
			raise TypeError("The argument 'filenames' must be "
							"an iterable of strings")

		params = []
		params_utf8 = []
		for tag, value in tags.items():
			params.append(u'-%s=%s' % (tag, value))

		params.extend(filenames)
		params_utf8 = [x.encode('utf-8') for x in params]
		return self.execute(*params_utf8)

	# ----------------------------------------------------------------------------------------------------------------------
	def set_tags(self, tags, filename):
		"""Writes the values of the specified tags for the given file.

		This is a convenience function derived from `set_tags_batch()`.
		Only difference is that it takes as last arugemnt only one file name
		as a string.
		"""
		return self.set_tags_batch(tags, [filename])

	# ----------------------------------------------------------------------------------------------------------------------
	def set_keywords_batch(self, mode, keywords, filenames):
		"""Modifies the keywords tag for the given files.

		The first argument is the operation mode:
		KW_REPLACE: Replace (i.e. set) the full keywords tag with `keywords`.
		KW_ADD:     Add `keywords` to the keywords tag.
					If a keyword is present, just keep it.
		KW_REMOVE:  Remove `keywords` from the keywords tag.
					If a keyword wasn't present, just leave it.

		The second argument is an iterable of key words.

		The third argument is an iterable of file names.

		The format of the return value is the same as for
		:py:meth:`execute()`.

		It can be passed into `check_ok()` and `format_error()`.
		"""
		# Explicitly ruling out strings here because passing in a
		# string would lead to strange and hard-to-find errors
		if isinstance(keywords, basestring):
			raise TypeError("The argument 'keywords' must be "
							"an iterable of strings")
		if isinstance(filenames, basestring):
			raise TypeError("The argument 'filenames' must be "
							"an iterable of strings")

		params = []
		params_utf8 = []

		kw_operation = {KW_REPLACE:"-%s=%s",
						KW_ADD:"-%s+=%s",
						KW_REMOVE:"-%s-=%s"}[mode]

		kw_params = [ kw_operation % (KW_TAGNAME, w)  for w in keywords ]

		params.extend(kw_params)
		params.extend(filenames)
		logging.debug (params)

		params_utf8 = [x.encode('utf-8') for x in params]
		return self.execute(*params_utf8)

	# ----------------------------------------------------------------------------------------------------------------------
	def set_keywords(self, mode, keywords, filename):
		"""Modifies the keywords tag for the given file.

		This is a convenience function derived from `set_keywords_batch()`.
		Only difference is that it takes as last argument only one file name
		as a string.
		"""
		return self.set_keywords_batch(mode, keywords, [filename])



	# ----------------------------------------------------------------------------------------------------------------------
	@staticmethod
	def _check_sanity_of_result(file_paths, result):
		"""
		Checks if the given file paths matches the 'SourceFile' entries in the result returned by
		exiftool. This is done to find possible mix ups in the streamed responses.
		"""
		# do some sanity checks on the results to make sure nothing was mixed up during reading from stdout
		if len(result) != len(file_paths):
			raise IOError("exiftool did return %d results, but expected was %d" % (len(result), len(file_paths)))
		for i in range(0, len(file_paths)):
			returned_source_file = result[i]['SourceFile']
			requested_file = file_paths[i]
			if returned_source_file != requested_file:
				raise IOError('exiftool returned data for file %s, but expected was %s'
							  % (returned_source_file, requested_file))

