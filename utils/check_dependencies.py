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
"""Script to check for the availability and version of dependencies."""

import re
import urllib2


def GetLibyalGoogleDriveVersion(library_name):
  """Retrieves the version number for a given libyal library on Google Drive.

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


def CheckLibyal(libyal_python_modules):
  """Checks the availability of libyal libraries.

  Args:
    libyal_python_modules: list of libyal python module names.

  Returns:
    True if the libyal libraries are available, false otherwise.
  """
  result = True
  for module_name, module_version in libyal_python_modules:
    try:
      module_object = map(__import__, [module_name])[0]
      module_loaded = True
    except ImportError:
      print u'[FAILURE]\tmissing: {0:s}.'.format(module_name)
      module_loaded = False
      result = False

    if module_loaded:
      libyal_name = u'lib{}'.format(module_name[2:])

      installed_version = int(module_object.get_version())
      try:
        latest_version = GetLibyalGoogleDriveVersion(libyal_name)
      except urllib2.URLError:
        print (
            u'Unable to verify version of {0:s} ({1:s}).\n'
            u'Does this system have Internet access?').format(
                libyal_name, module_name)
        result = False
        break

      if module_version is not None and installed_version < module_version:
        print (
            u'[FAILURE]\t{0:s} ({1:s}) version: {2:d} is too old, {3:d} or '
            u'later required.').format(
                libyal_name, module_name, installed_version, module_version)
        result = False

      elif installed_version != latest_version:
        print (
            u'[INFO]\t\t{0:s} ({1:s}) version: {2:d} installed, '
            u'version: {3:d} available.').format(
                libyal_name, module_name, installed_version, latest_version)

      else:
        print u'[OK]\t\t{0:s} ({1:s}) version: {2:d}'.format(
            libyal_name, module_name, installed_version)

  return result


def CheckPythonModule(
    module_name, version_attribute_name, minimum_version,
    maximum_version=None):
  """Checks the availability of a Python module.

  Args:
    module_name: the name of the module.
    version_attribute_name: the name of the attribute that contains the module
                            version.
    minimum_version: the minimum required version.
    maximum_version: the maximum required version. This attribute is optional
                     and should only be used if there is a recent API change
                     that prevents the tool from running if a later version
                     is used.

  Returns:
    True if the Python module is available and conforms to the minimum required
    version. False otherwise.
  """
  try:
    module_object = map(__import__, [module_name])[0]
  except ImportError:
    print u'[FAILURE]\tmissing: {0:s}.'.format(module_name)
    return False

  if version_attribute_name and minimum_version:
    module_version = getattr(module_object, version_attribute_name, None)

    if not module_version:
      return False

    # Split the version string and convert every digit into an integer.
    # A string compare of both version strings will yield an incorrect result.
    module_version_map = map(int, module_version.split('.'))
    minimum_version_map = map(int, minimum_version.split('.'))

    if module_version_map < minimum_version_map:
      print (
          u'[FAILURE]\t{0:s} version: {1:s} is too old, {2:s} or later '
          u'required.').format(module_name, module_version, minimum_version)
      return False

    if maximum_version:
      maximum_version_map = map(int, maximum_version.split('.'))
      if module_version_map > maximum_version_map:
        print (
            u'[FAILURE]\t{0:s} version: {1:s} is too recent, {2:s} or earlier '
            u'required.').format(module_name, module_version, maximum_version)
        return False

    print u'[OK]\t\t{0:s} version: {1:s}'.format(module_name, module_version)
  else:
    print u'[OK]\t\t{0:s}'.format(module_name)

  return True


def CheckPytsk():
  """Checks the availability of pytsk3.

  Returns:
    True if the pytsk3 Python module is available, false otherwise.
  """
  module_name = 'pytsk3'

  try:
    module_object = map(__import__, [module_name])[0]
  except ImportError:
    print u'[FAILURE]\tmissing: {0:s}.'.format(module_name)
    return False

  minimum_version = '4.1.2'
  module_version = module_object.TSK_VERSION_STR

  # Split the version string and convert every digit into an integer.
  # A string compare of both version strings will yield an incorrect result.
  module_version_map = map(int, module_version.split('.'))
  minimum_version_map = map(int, minimum_version.split('.'))
  if module_version_map < minimum_version_map:
    print (
        u'[FAILURE]\tSleuthKit version: {0:s} is too old, {1:s} or later '
        u'required.').format(module_version, minimum_version)
    return False

  print u'[OK]\t\tSleuthKit version: {0:s}'.format(module_version)

  minimum_version = '20140506'
  if not hasattr(module_object, 'get_version'):
    print u'[FAILURE]\t{0:s} is too old, {1:s} or later required.'.format(
        module_name, minimum_version)
    return False

  module_version = module_object.get_version()
  if module_version < minimum_version:
    print (
        u'[FAILURE]\t{0:s} version: {1:s} is too old, {2:s} or later '
        u'required.').format(module_name, module_version, minimum_version)
    return False

  print u'[OK]\t\t{0:s} version: {1:s}'.format(module_name, module_version)

  return True


if __name__ == '__main__':
  check_result = True
  print u'Checking availability and versions of plaso dependencies.'

  # The bencode module does not appear to have no version information.
  if not CheckPythonModule('bencode', '', ''):
    check_result = False

  if not CheckPythonModule('binplist', '__version__', '0.1.4'):
    check_result = False

  if not CheckPythonModule('six', '__version__', '1.1.0'):
    check_result = False

  if not CheckPythonModule(
      'psutil', '__version__', '1.2.1', maximum_version='1.2.1'):
    check_result = False

  if not CheckPythonModule('construct', '__version__', '2.5.2'):
    check_result = False

  if not CheckPythonModule('dpkt', '__version__', '1.8'):
    check_result = False

  if not CheckPythonModule('pyparsing', '__version__', '1.5.6'):
    check_result = False

  # TODO: determine the version of pytz.
  # pytz uses __version__ but has a different version indicator e.g. 2012d
  if not CheckPythonModule('pytz', '', ''):
    check_result = False

  # The protobuf module does not appear to have version information.
  if not CheckPythonModule('google.protobuf', '', ''):
    check_result = False

  if not CheckPythonModule('dfvfs', '__version__', '20140522'):
    check_result = False

  if not CheckPythonModule('sqlite3', 'sqlite_version', '3.7.8'):
    check_result = False

  if not CheckPythonModule('yaml', '__version__', '3.10'):
    check_result = False

  if not CheckPytsk():
    check_result = False

  libyal_check_result = CheckLibyal([
      ('pyesedb', 20140301),
      ('pyevt', None),
      ('pyevtx', None),
      ('pyewf', 20131210),
      ('pylnk', 20130304),
      ('pymsiecf', 20130317),
      ('pyolecf', 20131012),
      ('pyqcow', 20131204),
      ('pyregf', 20130716),
      ('pysmdev', 20140428),
      ('pyvhdi', 20131210),
      ('pyvmdk', 20140421),
      ('pyvshadow', 20131209),
  ])

  if not check_result:
    build_instructions_url = (
        u'https://sites.google.com/a/kiddaland.net/plaso/developer'
        u'/building-the-tool')

    print u'See: {0:s} on how to set up plaso.'.format(
        build_instructions_url)

  if not libyal_check_result:
    libyal_downloads_url = (
        u'https://googledrive.com/host/0B30H7z4S52FleW5vUHBnblJfcjg'
        u'/libyal.html')

    print u'Libyal libraries can be downloaded from here: {0:s}'.format(
        libyal_downloads_url)

  print u''
