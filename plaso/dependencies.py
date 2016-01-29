# -*- coding: utf-8 -*-
"""Functionality to check for the availability and version of dependencies."""

from __future__ import print_function
import re
import sys

# pylint: disable=no-name-in-module
if sys.version_info[0] < 3:
  # Keep urllib2 here since we this code should be able to be used
  # by a default Python set up.
  import urllib2 as urllib_error
  from urllib2 import urlopen
else:
  import urllib.error as urllib_error
  from urllib.request import urlopen


# The dictionary values are:
# module_name: minimum_version
LIBYAL_DEPENDENCIES = {
    u'pybde': 20140531,
    u'pyesedb': 20150409,
    u'pyevt': 20120410,
    u'pyevtx': 20141112,
    u'pyewf': 20131210,
    u'pyfsntfs': 20151130,
    u'pyfwsi': 20150606,
    u'pylnk': 20150830,
    u'pymsiecf': 20150314,
    u'pyolecf': 20151223,
    u'pyqcow': 20131204,
    u'pyregf': 20150315,
    u'pyscca': 20151226,
    u'pysigscan': 20150627,
    u'pysmdev': 20140529,
    u'pysmraw': 20140612,
    u'pyvhdi': 20131210,
    u'pyvmdk': 20140421,
    u'pyvshadow': 20160109}

# The tuple values are:
# module_name, version_attribute_name, minimum_version, maximum_version
PYTHON_DEPENDENCIES = [
    (u'artifacts', u'__version__', u'20150409', None),
    # The bencode module does not appear to have version information.
    (u'bencode', u'', u'', None),
    (u'binplist', u'__version__', u'0.1.4', None),
    (u'construct', u'__version__', u'2.5.2', None),
    (u'dateutil', u'__version__', u'1.5', None),
    (u'dfvfs', u'__version__', u'20160108', None),
    (u'dfwinreg', u'__version__', u'20160116', None),
    (u'dpkt', u'__version__', u'1.8', None),
    # The protobuf module does not appear to have version information.
    (u'google.protobuf', u'', u'', None),
    (u'hachoir_core', u'__version__', u'1.3.3', None),
    (u'hachoir_parser', u'__version__', u'1.3.4', None),
    (u'hachoir_metadata', u'__version__', u'1.3.3', None),
    (u'IPython', u'__version__', u'1.2.1', None),
    (u'pefile', u'__version__', u'1.2.10-139', None),
    (u'psutil', u'__version__', u'1.2.1', None),
    (u'pyparsing', u'__version__', u'2.0.3', None),
    # TODO: determine the version of pytz.
    # pytz uses __version__ but has a different version indicator e.g. 2012d
    (u'pytz', u'', u'', None),
    (u'requests', u'__version__', u'2.2.1', None),
    (u'six', u'__version__', u'1.1.0', None),
    (u'xlsxwriter', u'__version__', u'0.6.5', None),
    (u'yaml', u'__version__', u'3.10', None),
    (u'zmq', u'__version__', u'2.1.11', None)]

# The tuple values are:
# module_name, version_attribute_name, minimum_version, maximum_version
PYTHON_TEST_DEPENDENCIES = [
    (u'mock', u'__version__', u'0.7.1', None)]

_VERSION_SPLIT_REGEX = re.compile(r'\.|\-')


def _DownloadPageContent(download_url):
  """Downloads the page content.

  Args:
    download_url: the URL where to download the page content.

  Returns:
    The page content if successful, None otherwise.
  """
  if not download_url:
    return

  url_object = urlopen(download_url)
  if not url_object or url_object.code != 200:
    return

  return url_object.read()


def _ImportPythonModule(module_name):
  """Imports a Python module.

  Args:
    module_name: the name of the module.

  Returns:
    The Python module object (instance of module) or None
    if the module cannot be imported.
  """
  try:
    module_object = list(map(__import__, [module_name]))[0]
  except ImportError:
    return

  # If the module name contains dots get the upper most module object.
  if u'.' in module_name:
    for submodule_name in module_name.split(u'.')[1:]:
      module_object = getattr(module_object, submodule_name, None)

  return module_object


def _GetLibyalGithubReleasesLatestVersion(library_name):
  """Retrieves the latest version number of a libyal library on GitHub releases.

  Args:
    library_name: the name of the libyal library.

  Returns:
    The latest version for a given libyal library on GitHub releases
    or 0 on error.
  """
  download_url = (
      u'https://github.com/libyal/{0:s}/releases').format(library_name)

  page_content = _DownloadPageContent(download_url)
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
def _GetLibyalGoogleDriveLatestVersion(library_name):
  """Retrieves the latest version number of a libyal library on Google Drive.

  Args:
    library_name: the name of the libyal library.

  Returns:
    The latest version for a given libyal library on Google Drive
    or 0 on error.
  """
  download_url = u'https://code.google.com/p/{0:s}/'.format(library_name)

  page_content = _DownloadPageContent(download_url)
  if not page_content:
    return 0

  # The format of the library downloads URL is:
  # https://googledrive.com/host/{random string}/
  expression_string = (
      b'<a href="(https://googledrive.com/host/[^/]*/)"[^>]*>Downloads</a>')
  matches = re.findall(expression_string, page_content)

  if not matches or len(matches) != 1:
    return 0

  page_content = _DownloadPageContent(matches[0])
  if not page_content:
    return 0

  # The format of the library download URL is:
  # /host/{random string}/{library name}-{status-}{version}.tar.gz
  # Note that the status is optional and will be: beta, alpha or experimental.
  expression_string = b'/host/[^/]*/{0:s}-[a-z-]*([0-9]+)[.]tar[.]gz'.format(
      library_name)
  matches = re.findall(expression_string, page_content)

  if not matches:
    return 0

  return int(max(matches))


def _CheckLibyal(
    libyal_python_modules, latest_version_check=False, verbose_output=True):
  """Checks the availability of libyal libraries.

  Args:
    libyal_python_modules: a dictionary of libyal python module name as
                           the key and version as the value.
    latest_version_check: optional boolean value to indicate if the project
                          site should be checked for the latest version.
    verbose_output: optional boolean to indicate output should be verbose.

  Returns:
    True if the libyal libraries are available, False otherwise.
  """
  connection_error = False
  result = True
  for module_name, module_version in sorted(libyal_python_modules.items()):
    module_object = _ImportPythonModule(module_name)
    if not module_object:
      print(u'[FAILURE]\tmissing: {0:s}.'.format(module_name))
      result = False
      continue

    libyal_name = u'lib{0:s}'.format(module_name[2:])

    installed_version = int(module_object.get_version())

    latest_version = None
    if latest_version_check:
      try:
        latest_version = _GetLibyalGithubReleasesLatestVersion(libyal_name)
      except urllib_error.URLError:
        latest_version = None

      if not latest_version:
        try:
          latest_version = _GetLibyalGoogleDriveLatestVersion(libyal_name)
        except urllib_error.URLError:
          latest_version = None

      if not latest_version:
        print(
            u'Unable to determine latest version of {0:s} ({1:s}).\n'.format(
                libyal_name, module_name))
        latest_version = None
        connection_error = True

    if module_version is not None and installed_version < module_version:
      print((
          u'[FAILURE]\t{0:s} ({1:s}) version: {2:d} is too old, {3:d} or '
          u'later required.').format(
              libyal_name, module_name, installed_version, module_version))
      result = False

    elif verbose_output:
      if latest_version and installed_version != latest_version:
        print((
            u'[INFO]\t\t{0:s} ({1:s}) version: {2:d} installed, '
            u'version: {3:d} available.').format(
                libyal_name, module_name, installed_version, latest_version))

      else:
        print(u'[OK]\t\t{0:s} ({1:s}) version: {2:d}'.format(
            libyal_name, module_name, installed_version))

  if connection_error:
    print((
        u'[INFO] to check for the latest versions this script needs Internet '
        u'access.'))

  return result


def _CheckPythonModule(
    module_name, version_attribute_name, minimum_version,
    maximum_version=None, verbose_output=True):
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
    verbose_output: optional boolean to indicate output should be verbose.

  Returns:
    True if the Python module is available and conforms to the minimum required
    version. False otherwise.
  """
  module_object = _ImportPythonModule(module_name)
  if not module_object:
    print(u'[FAILURE]\tmissing: {0:s}.'.format(module_name))
    return False

  if not version_attribute_name or not minimum_version:
    if verbose_output:
      print(u'[OK]\t\t{0:s}'.format(module_name))
    return True

  module_version = getattr(module_object, version_attribute_name, None)
  if not module_version:
    print((
        u'[FAILURE]\tunable to determine version information '
        u'for: {0:s}').format(module_name))
    return False

  # Split the version string and convert every digit into an integer.
  # A string compare of both version strings will yield an incorrect result.
  module_version_map = list(
      map(int, _VERSION_SPLIT_REGEX.split(module_version)))
  minimum_version_map = list(
      map(int, _VERSION_SPLIT_REGEX.split(minimum_version)))

  if module_version_map < minimum_version_map:
    print((
        u'[FAILURE]\t{0:s} version: {1:s} is too old, {2:s} or later '
        u'required.').format(module_name, module_version, minimum_version))
    return False

  if maximum_version:
    maximum_version_map = list(
        map(int, _VERSION_SPLIT_REGEX.split(maximum_version)))
    if module_version_map > maximum_version_map:
      print((
          u'[FAILURE]\t{0:s} version: {1:s} is too recent, {2:s} or earlier '
          u'required.').format(module_name, module_version, maximum_version))
      return False

  if verbose_output:
    print(u'[OK]\t\t{0:s} version: {1:s}'.format(module_name, module_version))

  return True


def _CheckPytsk(verbose_output=True):
  """Checks the availability of pytsk.

  Args:
    verbose_output: optional boolean to indicate output should be verbose.

  Returns:
    True if the pytsk Python module is available, False otherwise.
  """
  module_name = u'pytsk3'
  minimum_version_libtsk = u'4.1.2'
  minimum_version_pytsk = u'20140506'

  module_object = _ImportPythonModule(module_name)
  if not module_object:
    print(u'[FAILURE]\tmissing: {0:s}.'.format(module_name))
    return False

  module_version = module_object.TSK_VERSION_STR

  # Split the version string and convert every digit into an integer.
  # A string compare of both version strings will yield an incorrect result.
  module_version_map = list(map(int, module_version.split(u'.')))
  minimum_version_map = list(map(int, minimum_version_libtsk.split(u'.')))
  if module_version_map < minimum_version_map:
    print((
        u'[FAILURE]\tSleuthKit (libtsk) version: {0:s} is too old, {1:s} or '
        u'later required.').format(module_version, minimum_version_libtsk))
    return False

  if verbose_output:
    print(u'[OK]\t\tSleuthKit version: {0:s}'.format(module_version))

  if not hasattr(module_object, u'get_version'):
    print(u'[FAILURE]\t{0:s} is too old, {1:s} or later required.'.format(
        module_name, minimum_version_pytsk))
    return False

  module_version = module_object.get_version()
  if module_version < minimum_version_pytsk:
    print((
        u'[FAILURE]\t{0:s} version: {1:s} is too old, {2:s} or later '
        u'required.').format(
            module_name, module_version, minimum_version_pytsk))
    return False

  if verbose_output:
    print(u'[OK]\t\t{0:s} version: {1:s}'.format(module_name, module_version))

  return True


def _CheckSqlite3(verbose_output=True):
  """Checks the availability of sqlite3.

  Args:
    verbose_output: optional boolean to indicate output should be verbose.

  Returns:
    True if the sqlite3 Python module is available, False otherwise.
  """
  # On Windows sqlite3 can be provided by both pysqlite2.dbapi2 and
  # sqlite3. sqlite3 is provided with the Python installation and
  # pysqlite2.dbapi2 by the pysqlite2 Python module. Typically
  # pysqlite2.dbapi2 would contain a newer version of sqlite3, hence
  # we check for its presence first.
  module_name = u'pysqlite2.dbapi2'
  minimum_version = u'3.7.8'

  module_object = _ImportPythonModule(module_name)
  if not module_object:
    module_name = u'sqlite3'

  module_object = _ImportPythonModule(module_name)
  if not module_object:
    print(u'[FAILURE]\tmissing: {0:s}.'.format(module_name))
    return False

  module_version = getattr(module_object, u'sqlite_version', None)
  if not module_version:
    return False

  # Split the version string and convert every digit into an integer.
  # A string compare of both version strings will yield an incorrect result.
  module_version_map = list(
      map(int, _VERSION_SPLIT_REGEX.split(module_version)))
  minimum_version_map = list(
      map(int, _VERSION_SPLIT_REGEX.split(minimum_version)))

  if module_version_map < minimum_version_map:
    print((
        u'[FAILURE]\t{0:s} version: {1:s} is too old, {2:s} or later '
        u'required.').format(module_name, module_version, minimum_version))
    return False

  if verbose_output:
    print(u'[OK]\t\t{0:s} version: {1:s}'.format(module_name, module_version))

  return True


def CheckDependencies(latest_version_check=False, verbose_output=True):
  """Checks the availability of the dependencies.

  Args:
    latest_version_check: optional boolean value to indicate if the project
                          site should be checked for the latest version.
    verbose_output: optional boolean to indicate output should be verbose.

  Returns:
    True if the dependencies are available, False otherwise.
  """
  print(u'Checking availability and versions of plaso dependencies.')
  check_result = True

  for values in PYTHON_DEPENDENCIES:
    if not _CheckPythonModule(
        values[0], values[1], values[2], maximum_version=values[3],
        verbose_output=verbose_output):
      check_result = False

  if not _CheckSqlite3(verbose_output=verbose_output):
    check_result = False

  if not _CheckPytsk(verbose_output=verbose_output):
    check_result = False

  libyal_check_result = _CheckLibyal(
      LIBYAL_DEPENDENCIES, latest_version_check=latest_version_check,
      verbose_output=verbose_output)

  if not libyal_check_result:
    check_result = False

  if check_result and not verbose_output:
    print(u'[OK]')

  print(u'')
  return check_result


def CheckModuleVersion(module_name):
  """Checks the version requirements of a module.

  Args:
    module_name: the name of the module.

  Raises:
    ImportError: if the module does not exists or does not meet
                 the version requirements.
  """
  # TODO: add support for non libyal dependencies.
  if module_name not in LIBYAL_DEPENDENCIES:
    return

  try:
    module_object = list(map(__import__, [module_name]))[0]
  except ImportError:
    raise

  module_version = module_object.get_version()
  try:
    module_version = int(module_version, 10)
  except ValueError:
    raise ImportError(u'Unable to determine version of module {0:s}')

  if module_version < LIBYAL_DEPENDENCIES[module_name]:
    raise ImportError(
        u'Module {0:s} is too old, minimum required version {1!s}'.format(
            module_name, module_version))


def CheckTestDependencies(latest_version_check=False):
  """Checks the availability of the dependencies when running tests.

  Args:
    latest_version_check: optional boolean value to indicate if the project
                          site should be checked for the latest version.

  Returns:
    True if the dependencies are available, False otherwise.
  """
  if not CheckDependencies(latest_version_check=latest_version_check):
    return False

  print(u'Checking availability and versions of plaso test dependencies.')
  for values in PYTHON_TEST_DEPENDENCIES:
    if not _CheckPythonModule(
        values[0], values[1], values[2], maximum_version=values[3]):
      return False

  return True


def GetInstallRequires():
  """Returns the install_requires for setup.py"""
  install_requires = []
  for values in PYTHON_DEPENDENCIES:
    module_name = values[0]
    module_version = values[2]

    # Map the import name to the pypi name.
    if module_name == u'yaml':
      module_name = u'PyYAML'
    elif module_name == u'sqlite3':
      # Override the pysqlite version since it does not match
      # the sqlite3 version.
      module_name = u'pysqlite'
      module_version = None

    if not module_version:
      install_requires.append(module_name)
    else:
      install_requires.append(u'{0:s} >= {1:s}'.format(
          module_name, module_version))

  install_requires.append(u'pytsk3 >= 4.1.2')

  for module_name, module_version in sorted(LIBYAL_DEPENDENCIES.items()):
    if not module_version:
      install_requires.append(module_name)
    else:
      install_requires.append(u'{0:s} >= {1:d}'.format(
          module_name, module_version))

  return sorted(install_requires)
