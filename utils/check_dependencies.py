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


def DownloadPageContent(download_url):
  """Downloads the page content.

  Args:
    download_url: the URL where to download the page content.

  Returns:
    The page content if successful, None otherwise.
  """
  if not download_url:
    return

  url_object = urllib2.urlopen(download_url)

  if url_object.code != 200:
    return

  return url_object.read()


def GetLibyalGithubReleasesLatestVersion(library_name):
  """Retrieves the latest version number of a libyal library on GitHub releases.

  Args:
    library_name: the name of the libyal library.

  Returns:
    The latest version for a given libyal library on GitHub releases
    or 0 on error.
  """
  download_url = (
      u'https://github.com/libyal/{0:s}/releases').format(library_name)

  page_content = DownloadPageContent(download_url)
  if not page_content:
    return 0

  # The format of the project download URL is:
  # /libyal/{project name}/releases/download/{git tag}/
  # {project name}{status-}{version}.tar.gz
  # Note that the status is optional and will be: beta, alpha or experimental.
  expression_string = (
      u'/libyal/{0:s}/releases/download/[^/]*/{0:s}-[a-z-]*([0-9]+)'
      u'[.]tar[.]gz').format(library_name)
  matches = re.findall(expression_string, page_content)

  if not matches:
    return 0

  return int(max(matches))


# TODO: Remove when Google Drive support is no longer needed.
def GetLibyalGoogleDriveLatestVersion(library_name):
  """Retrieves the latest version number of a libyal library on Google Drive.

  Args:
    library_name: the name of the libyal library.

  Returns:
    The latest version for a given libyal library on Google Drive
    or 0 on error.
  """
  download_url = 'https://code.google.com/p/{0:s}/'.format(library_name)

  page_content = DownloadPageContent(download_url)
  if not page_content:
    return 0

  # The format of the library downloads URL is:
  # https://googledrive.com/host/{random string}/
  expression_string = (
      '<a href="(https://googledrive.com/host/[^/]*/)"[^>]*>Downloads</a>')
  matches = re.findall(expression_string, page_content)

  if not matches or len(matches) != 1:
    return 0

  page_content = DownloadPageContent(matches[0])
  if not page_content:
    return 0

  # The format of the library download URL is:
  # /host/{random string}/{library name}-{status-}{version}.tar.gz
  # Note that the status is optional and will be: beta, alpha or experimental.
  expression_string = '/host/[^/]*/{0:s}-[a-z-]*([0-9]+)[.]tar[.]gz'.format(
      library_name)
  matches = re.findall(expression_string, page_content)

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
  connection_error = False
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
      libyal_name = u'lib{0:s}'.format(module_name[2:])

      installed_version = int(module_object.get_version())
      try:
        latest_version = GetLibyalGithubReleasesLatestVersion(libyal_name)
      except urllib2.URLError:
        latest_version = 0

      if not latest_version:
        try:
          latest_version = GetLibyalGoogleDriveLatestVersion(libyal_name)
        except urllib2.URLError:
          latest_version = 0

      if not latest_version:
        print (
            u'Unable to determine latest version of {0:s} ({1:s}).\n').format(
                libyal_name, module_name)
        latest_version = None
        connection_error = True

      if module_version is not None and installed_version < module_version:
        print (
            u'[FAILURE]\t{0:s} ({1:s}) version: {2:d} is too old, {3:d} or '
            u'later required.').format(
                libyal_name, module_name, installed_version, module_version)
        result = False

      elif latest_version and installed_version != latest_version:
        print (
            u'[INFO]\t\t{0:s} ({1:s}) version: {2:d} installed, '
            u'version: {3:d} available.').format(
                libyal_name, module_name, installed_version, latest_version)

      else:
        print u'[OK]\t\t{0:s} ({1:s}) version: {2:d}'.format(
            libyal_name, module_name, installed_version)

  if connection_error:
    print (
        u'[INFO] to check for the latest versions this script needs Internet '
        u'access.')

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

  if not CheckPythonModule('construct', '__version__', '2.5.2'):
    check_result = False

  if not CheckPythonModule('dateutil.parser', '', ''):
    check_result = False

  if not CheckPythonModule('dfvfs', '__version__', '20150210'):
    check_result = False

  if not CheckPythonModule('dpkt', '__version__', '1.8'):
    check_result = False

  # The protobuf module does not appear to have version information.
  if not CheckPythonModule('google.protobuf', '', ''):
    check_result = False

  if not CheckPythonModule('hachoir_core', '__version__', '1.3.3'):
    check_result = False

  if not CheckPythonModule('hachoir_parser', '__version__', '1.3.4'):
    check_result = False

  if not CheckPythonModule('hachoir_metadata', '__version__', '1.3.3'):
    check_result = False

  if not CheckPythonModule('IPython', '__version__', '1.2.1'):
    check_result = False

  if not CheckPythonModule('yaml', '__version__', '3.10'):
    check_result = False

  if not CheckPythonModule('psutil', '__version__', '1.2.1'):
    check_result = False

  if not CheckPythonModule('pyparsing', '__version__', '2.0.2'):
    check_result = False

  # TODO: determine the version of pytz.
  # pytz uses __version__ but has a different version indicator e.g. 2012d
  if not CheckPythonModule('pytz', '', ''):
    check_result = False

  if not CheckPythonModule('six', '__version__', '1.1.0'):
    check_result = False

  if not CheckPythonModule('sqlite3', 'sqlite_version', '3.7.8'):
    check_result = False

  if not CheckPytsk():
    check_result = False

  libyal_check_result = CheckLibyal([
      ('pybde', 20140531),
      ('pyesedb', 20140301),
      ('pyevt', None),
      ('pyevtx', 20141112),
      ('pyewf', 20131210),
      ('pyfwsi', 20140714),
      ('pylnk', 20141026),
      ('pymsiecf', 20130317),
      ('pyolecf', 20131012),
      ('pyqcow', 20131204),
      ('pyregf', 20130716),
      ('pysigscan', 20150114),
      ('pysmdev', 20140529),
      ('pysmraw', 20140612),
      ('pyvhdi', 20131210),
      ('pyvmdk', 20140421),
      ('pyvshadow', 20131209),
  ])

  if not libyal_check_result:
    check_result = False

  if not check_result:
    build_instructions_url = (
        u'https://sites.google.com/a/kiddaland.net/plaso/developer'
        u'/building-the-tool')

    print u'See: {0:s} on how to set up plaso.'.format(
        build_instructions_url)

  print u''
