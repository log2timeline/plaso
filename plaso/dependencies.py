# -*- coding: utf-8 -*-
"""Functionality to check for the availability and version of dependencies."""

from __future__ import print_function
import re


# Dictionary that contains version tuples per module name.
#
# A version tuple consists of:
# (version_attribute_name, minimum_version, maximum_version, is_required)
#
# Where version_attribute_name is either a name of an attribute,
# property or method.
PYTHON_DEPENDENCIES = {
    u'artifacts': (u'__version__', u'20161022', None, True),
    # The bencode module does not appear to have version information.
    u'bencode': (u'', u'', None, True),
    u'binplist': (u'__version__', u'0.1.4', None, True),
    u'construct': (u'__version__', u'2.5.2', u'2.5.3', True),
    u'Crypto': (u'__version__', u'2.6.0', None, True),
    u'dateutil': (u'__version__', u'1.5', None, True),
    u'dfdatetime': (u'__version__', u'20170103', None, True),
    u'dfvfs': (u'__version__', u'20160803', None, True),
    u'dfwinreg': (u'__version__', u'20160320', None, True),
    u'dpkt': (u'__version__', u'1.8', None, True),
    # TODO: determine the version of Efilter.
    u'efilter': (u'', u'1.5', None, True),
    u'hachoir_core': (u'__version__', u'1.3.3', None, True),
    u'hachoir_metadata': (u'__version__', u'1.3.3', None, True),
    u'hachoir_parser': (u'__version__', u'1.3.4', None, True),
    u'lzma': (u'__version__', u'0.5.3', None, False),
    u'pefile': (u'__version__', u'1.2.10-139', None, True),
    u'psutil': (u'__version__', u'1.2.1', None, True),
    u'pybde': (u'get_version()', u'20140531', None, True),
    u'pyesedb': (u'get_version()', u'20150409', None, True),
    u'pyevt': (u'get_version()', u'20120410', None, True),
    u'pyevtx': (u'get_version()', u'20141112', None, True),
    u'pyewf': (u'get_version()', u'20131210', None, True),
    u'pyfsntfs': (u'get_version()', u'20151130', None, True),
    u'pyfvde': (u'get_version()', u'20160719', None, True),
    u'pyfwnt': (u'get_version()', u'20160418', None, True),
    u'pyfwsi': (u'get_version()', u'20150606', None, True),
    u'pylnk': (u'get_version()', u'20150830', None, True),
    u'pymsiecf': (u'get_version()', u'20150314', None, True),
    u'pyolecf': (u'get_version()', u'20151223', None, True),
    u'pyparsing': (u'__version__', u'2.0.3', None, True),
    u'pyqcow': (u'get_version()', u'20131204', None, True),
    u'pyregf': (u'get_version()', u'20150315', None, True),
    u'pyscca': (u'get_version()', u'20161031', None, True),
    u'pysigscan': (u'get_version()', u'20150627', None, True),
    u'pysmdev': (u'get_version()', u'20140529', None, True),
    u'pysmraw': (u'get_version()', u'20140612', None, True),
    u'pytsk3': (u'get_version()', u'20160721', None, True),
    # TODO: determine the version of pytz.
    # pytz uses __version__ but has a different version indicator e.g. 2012d
    u'pytz': (u'', u'', None, True),
    u'pyvhdi': (u'get_version()', u'20131210', None, True),
    u'pyvmdk': (u'get_version()', u'20140421', None, True),
    u'pyvshadow': (u'get_version()', u'20160109', None, True),
    u'pyvslvm': (u'get_version()', u'20160109', None, True),
    u'requests': (u'__version__', u'2.2.1', None, True),
    u'six': (u'__version__', u'1.1.0', None, True),
    u'xlsxwriter': (u'__version__', u'0.9.3', None, True),
    u'yaml': (u'__version__', u'3.10', None, True),
    u'yara': (u'YARA_VERSION', u'3.4.0', None, True),
    u'zmq': (u'__version__', u'2.1.11', None, True)}

_VERSION_SPLIT_REGEX = re.compile(r'\.|\-')


def _CheckPythonModule(
    module_name, version_attribute_name, minimum_version,
    is_required=True, maximum_version=None, verbose_output=True):
  """Checks the availability of a Python module.

  Args:
    module_name (str): name of the module.
    version_attribute_name (str): name of the attribute that contains
       the module version or method to retrieve the module version.
    minimum_version (str): minimum required version.
    is_required (Optional[bool]): True if the Python module is a required
        dependency.
    maximum_version (Optional[str]): maximum required version. Should only be
        used if there is a later version that is not supported.
    verbose_output (Optional[bool]): True if output should be verbose.

  Returns:
    bool: True if the Python module is available and conforms to
        the minimum required version, False otherwise.
  """
  module_object = _ImportPythonModule(module_name)
  if not module_object:
    if not is_required:
      print(u'[OPTIONAL]\tmissing: {0:s}.'.format(module_name))
      return True

    print(u'[FAILURE]\tmissing: {0:s}.'.format(module_name))
    return False

  if not version_attribute_name or not minimum_version:
    if verbose_output:
      print(u'[OK]\t\t{0:s}'.format(module_name))
    return True

  module_version = None
  if not version_attribute_name.endswith(u'()'):
    module_version = getattr(module_object, version_attribute_name, None)
  else:
    version_method = getattr(module_object, version_attribute_name[:-2], None)
    if version_method:
      module_version = version_method()

  if not module_version:
    print((
        u'[FAILURE]\tunable to determine version information '
        u'for: {0:s}').format(module_name))
    return False

  # Make sure the module version is a string.
  module_version = u'{0!s}'.format(module_version)

  # Split the version string and convert every digit into an integer.
  # A string compare of both version strings will yield an incorrect result.
  module_version_map = list(
      map(int, _VERSION_SPLIT_REGEX.split(module_version)))
  minimum_version_map = list(
      map(int, _VERSION_SPLIT_REGEX.split(minimum_version)))

  if module_version_map < minimum_version_map:
    print((
        u'[FAILURE]\t{0:s} version: {1!s} is too old, {2!s} or later '
        u'required.').format(module_name, module_version, minimum_version))
    return False

  if maximum_version:
    maximum_version_map = list(
        map(int, _VERSION_SPLIT_REGEX.split(maximum_version)))
    if module_version_map > maximum_version_map:
      print((
          u'[FAILURE]\t{0:s} version: {1!s} is too recent, {2!s} or earlier '
          u'required.').format(module_name, module_version, maximum_version))
      return False

  if verbose_output:
    print(u'[OK]\t\t{0:s} version: {1!s}'.format(module_name, module_version))

  return True


def _CheckSQLite3(verbose_output=True):
  """Checks the availability of sqlite3.

  Args:
    verbose_output (Optional[bool]): True if output should be verbose.

  Returns:
    bool: True if the sqlite3 Python module is available, False otherwise.
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
        u'[FAILURE]\t{0:s} version: {1!s} is too old, {2!s} or later '
        u'required.').format(module_name, module_version, minimum_version))
    return False

  if verbose_output:
    print(u'[OK]\t\t{0:s} version: {1!s}'.format(module_name, module_version))

  return True


def _ImportPythonModule(module_name):
  """Imports a Python module.

  Args:
    module_name (str): name of the module.

  Returns:
    module: Python module or None if the module cannot be imported.
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


def CheckDependencies(verbose_output=True):
  """Checks the availability of the dependencies.

  Args:
    verbose_output (Optional[bool]): True if output should be verbose.

  Returns:
    bool: True if the dependencies are available, False otherwise.
  """
  print(u'Checking availability and versions of dependencies.')
  check_result = True

  for module_name, version_tuple in sorted(PYTHON_DEPENDENCIES.items()):
    if not _CheckPythonModule(
        module_name, version_tuple[0], version_tuple[1],
        is_required=version_tuple[3], maximum_version=version_tuple[2],
        verbose_output=verbose_output):
      check_result = False

  if not _CheckSQLite3(verbose_output=verbose_output):
    check_result = False

  if check_result and not verbose_output:
    print(u'[OK]')

  print(u'')
  return check_result
