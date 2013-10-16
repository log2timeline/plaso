#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains simple checks for versions of dependent tools."""

import re
import sys
import urllib2

LIBRARIES = [
    'pyevt', 'pyevtx', 'pylnk', 'pymsiecf', 'pyolecf', 'pyregf', 'pyvshadow']


def CheckLibyalGoogleDriveVersion(library_name):
  """Returns the version number for a given libyal library on Google Drive.

  Args:
    library_name: the name of the libyal library.

  Returns:
    The latest version for a given libyal library on Google Drive
    or 0 on error.
  """
  url = 'https://code.google.com/p/{0}/'.format(library_name)

  url_object = urllib2.urlopen(url)

  if url_object.code != 200:
    return None

  data = url_object.read()

  # The format of the library downloads URL is:
  # https://googledrive.com/host/{random string}/
  expression_string = (
      '<a href="(https://googledrive.com/host/[^/]*/)"[^>]*>Downloads</a>')
  matches = re.findall(expression_string, data)

  if not matches or len(matches) != 1:
    return 0

  url_object = urllib2.urlopen(matches[0])

  if url_object.code != 200:
    return 0

  data = url_object.read()

  # The format of the library download URL is:
  # /host/{random string}/{library name}-{status-}{version}.tar.gz
  # Note that the status is optional and will be: beta, alpha or experimental.
  expression_string = '/host/[^/]*/{0}-[a-z-]*([0-9]+)[.]tar[.]gz'.format(
      library_name)
  matches = re.findall(expression_string, data)

  if not matches:
    return 0

  return int(max(matches))


def CheckVersion(library):
  """Return the version number for a given library."""
  url = urllib2.urlopen('http://code.google.com/p/{}/downloads/list'.format(
      library))
  if url.code != 200:
    return 0

  library_re = re.compile(' ({}.+tar.gz)'.format(library), re.I)
  data = url.read()
  m = library_re.search(data)
  if not m:
    return 0

  _, _, end_part = m.group(1).rpartition('-')
  version, _, _ = end_part.partition('.')

  return int(version)


if __name__ == '__main__':
  print 'Loading libraries'
  library_url = (
      'https://googledrive.com/host/0B30H7z4S52FleW5vUHBnblJfcjg/libyal.html')

  try:
    parser_libraries = map(__import__, LIBRARIES)
  except ImportError as error_message:
    error_words = str(error_message).split()
    py_library_name = error_words[-1]
    lib_library_name = 'lib{}'.format(py_library_name[3:])

    print (
        u'Unable to proceed. You are missing an important library: {} '
        u'[{}]').format(
            lib_library_name, py_library_name)
    print 'Libraries can be downloaded from here: {}'.format(library_url)
    sys.exit(1)

  mismatch = False
  for python_binding in parser_libraries:
    libname = 'lib{}'.format(python_binding.__name__[2:])
    installed_version = int(python_binding.get_version())
    available_version = CheckLibyalGoogleDriveVersion(libname)

    if installed_version != available_version:
      mismatch = True
      print '  [{}] Version mismatch: installed {}, available: {}'.format(
          libname, installed_version, available_version)
    else:
      print '  [{}] OK'.format(libname)

  if mismatch:
    print '\nLibraries can be downloaded from here: {}'.format(library_url)
