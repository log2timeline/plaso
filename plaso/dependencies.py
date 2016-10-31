# -*- coding: utf-8 -*-
"""Functionality to check for the availability and version of dependencies."""

from __future__ import print_function
import re


# Dictionary that contains version tuples per module name.
#
# A version tuple consists of:
# (version_attribute_name, minimum_version, maximum_version)
#
# Where ersion_attribute_name is either a name of an attribute,
# property or method.
PYTHON_DEPENDENCIES = {
    u'artifacts': (u'__version__', u'20150409', None),
    # The bencode module does not appear to have version information.
    u'bencode': (u'', u'', None),
    u'binplist': (u'__version__', u'0.1.4', None),
    u'construct': (u'__version__', u'2.5.2', u'2.5.3'),
    u'Crypto': (u'__version__', u'2.6.0', None),
    u'dateutil': (u'__version__', u'1.5', None),
    u'dfdatetime': (u'__version__', u'20160319', None),
    u'dfvfs': (u'__version__', u'20160803', None),
    u'dfwinreg': (u'__version__', u'20160320', None),
    u'dpkt': (u'__version__', u'1.8', None),
    # TODO: determine the version of Efilter.
    u'efilter': (u'', u'1.5', None),
    u'hachoir_core': (u'__version__', u'1.3.3', None),
    u'hachoir_metadata': (u'__version__', u'1.3.3', None),
    u'hachoir_parser': (u'__version__', u'1.3.4', None),
    u'IPython': (u'__version__', u'1.2.1', None),
    u'pefile': (u'__version__', u'1.2.10-139', None),
    u'psutil': (u'__version__', u'1.2.1', None),
    u'pybde': (u'get_version()', u'20140531', None),
    u'pyesedb': (u'get_version()', u'20150409', None),
    u'pyevt': (u'get_version()', u'20120410', None),
    u'pyevtx': (u'get_version()', u'20141112', None),
    u'pyewf': (u'get_version()', u'20131210', None),
    u'pyfsntfs': (u'get_version()', u'20151130', None),
    u'pyfvde': (u'get_version()', u'20160719', None),
    u'pyfwnt': (u'get_version()', u'20160418', None),
    u'pyfwsi': (u'get_version()', u'20150606', None),
    u'pylnk': (u'get_version()', u'20150830', None),
    u'pymsiecf': (u'get_version()', u'20150314', None),
    u'pyolecf': (u'get_version()', u'20151223', None),
    u'pyparsing': (u'__version__', u'2.0.3', None),
    u'pyqcow': (u'get_version()', u'20131204', None),
    u'pyregf': (u'get_version()', u'20150315', None),
    u'pyscca': (u'get_version()', u'20151226', None),
    u'pysigscan': (u'get_version()', u'20150627', None),
    u'pysmdev': (u'get_version()', u'20140529', None),
    u'pysmraw': (u'get_version()', u'20140612', None),
    u'pytsk3': (u'get_version()', u'20160721', None),
    # TODO: determine the version of pytz.
    # pytz uses __version__ but has a different version indicator e.g. 2012d
    u'pytz': (u'', u'', None),
    u'pyvhdi': (u'get_version()', u'20131210', None),
    u'pyvmdk': (u'get_version()', u'20140421', None),
    u'pyvshadow': (u'get_version()', u'20160109', None),
    u'pyvslvm': (u'get_version()', u'20160109', None),
    u'requests': (u'__version__', u'2.2.1', None),
    u'six': (u'__version__', u'1.1.0', None),
    u'xlsxwriter': (u'__version__', u'0.9.3', None),
    u'yaml': (u'__version__', u'3.10', None),
    u'yara': (u'YARA_VERSION', u'3.4.0', None),
    u'zmq': (u'__version__', u'2.1.11', None)}

PYTHON_TEST_DEPENDENCIES = {
    u'mock': (u'__version__', u'0.7.1', None)}

# Maps Python module names to DPKG packages.
_DPKG_PACKAGE_NAMES = {
    u'Crypto': u'python-crypto',
    u'hachoir_core': u'python-hachoir-core',
    u'hachoir_metadata': u'python-hachoir-metadata',
    u'hachoir_parser': u'python-hachoir-parser',
    u'IPython': u'ipython',
    u'pybde': u'libbde-python',
    u'pyesedb': u'libesedb-python',
    u'pyevt': u'libevt-python',
    u'pyevtx': u'libevtx-python',
    u'pyewf': u'libewf-python',
    u'pyfsntfs': u'libfsntfs-python',
    u'pyfvde': u'libfvde-python',
    u'pyfwnt': u'libfwnt-python',
    u'pyfwsi': u'libfwsi-python',
    u'pylnk': u'liblnk-python',
    u'pymsiecf': u'libmsiecf-python',
    u'pyolecf': u'libolecf-python',
    u'pyqcow': u'libqcow-python',
    u'pyregf': u'libregf-python',
    u'pyscca': u'libscca-python',
    u'pysigscan': u'libsigscan-python',
    u'pysmdev': u'libsmdev-python',
    u'pysmraw': u'libsmraw-python',
    u'pytz': u'python-tz',
    u'pyvhdi': u'libvhdi-python',
    u'pyvmdk': u'libvmdk-python',
    u'pyvshadow': u'libvshadow-python',
    u'pyvslvm': u'libvslvm-python'}

# Maps Python module names to PyPI projects.
_PYPI_PROJECT_NAMES = {
    u'Crypto': u'pycrypto',
    u'dateutil': u'python-dateutil',
    u'hachoir_core': u'hachoir-core',
    u'hachoir_metadata': u'hachoir-metadata',
    u'hachoir_parser': u'hachoir-parser',
    u'pybde': u'libbde-python',
    u'pyesedb': u'libesedb-python',
    u'pyevt': u'libevt-python',
    u'pyevtx': u'libevtx-python',
    u'pyewf': u'libewf-python',
    u'pyfsntfs': u'libfsntfs-python',
    u'pyfvde': u'libfvde-python',
    u'pyfwnt': u'libfwnt-python',
    u'pyfwsi': u'libfwsi-python',
    u'pylnk': u'liblnk-python',
    u'pymsiecf': u'libmsiecf-python',
    u'pyolecf': u'libolecf-python',
    u'pyqcow': u'libqcow-python',
    u'pyregf': u'libregf-python',
    u'pyscca': u'libscca-python',
    u'pysigscan': u'libsigscan-python',
    u'pysmdev': u'libsmdev-python',
    u'pysmraw': u'libsmraw-python',
    u'pyvhdi': u'libvhdi-python',
    u'pyvmdk': u'libvmdk-python',
    u'pyvshadow': u'libvshadow-python',
    u'pyvslvm': u'libvslvm-python',
    u'sqlite3': u'pysqlite',
    u'yaml': u'PyYAML',
    u'yara': u'yara-python',
    u'xlsxwriter': u'XlsxWriter',
    u'zmq': u'pyzmq'}

# Maps Python module names to RPM packages.
_RPM_PACKAGE_NAMES = {
    u'Crypto': u'python-crypto',
    u'hachoir_core': u'python-hachoir-core',
    u'hachoir_metadata': u'python-hachoir-metadata',
    u'hachoir_parser': u'python-hachoir-parser',
    u'IPython': u'python-ipython',
    u'pybde': u'libbde-python',
    u'pyesedb': u'libesedb-python',
    u'pyevt': u'libevt-python',
    u'pyevtx': u'libevtx-python',
    u'pyewf': u'libewf-python',
    u'pyfsntfs': u'libfsntfs-python',
    u'pyfvde': u'libfvde-python',
    u'pyfwnt': u'libfwnt-python',
    u'pyfwsi': u'libfwsi-python',
    u'pylnk': u'liblnk-python',
    u'pymsiecf': u'libmsiecf-python',
    u'pyolecf': u'libolecf-python',
    u'pyqcow': u'libqcow-python',
    u'pyregf': u'libregf-python',
    u'pyscca': u'libscca-python',
    u'pysigscan': u'libsigscan-python',
    u'pysmdev': u'libsmdev-python',
    u'pysmraw': u'libsmraw-python',
    u'pytz': u'pytz',
    u'pyvhdi': u'libvhdi-python',
    u'pyvmdk': u'libvmdk-python',
    u'pyvshadow': u'libvshadow-python',
    u'pyvslvm': u'libvslvm-python',
    u'sqlite3': u'python-libs'}

_VERSION_SPLIT_REGEX = re.compile(r'\.|\-')


def _CheckPythonModule(
    module_name, version_attribute_name, minimum_version,
    maximum_version=None, verbose_output=True):
  """Checks the availability of a Python module.

  Args:
    module_name (str): name of the module.
    version_attribute_name (str): name of the attribute that contains
       the module version or method to retrieve the module version.
    minimum_version (str): minimum required version.
    maximum_version (Optional[str]): maximum required version. Should only be
        used if there is a later version that is not supported.
    verbose_output (Optional[bool]): True if output should be verbose.

  Returns:
    bool: True if the Python module is available and conforms to
        the minimum required version, False otherwise.
  """
  module_object = _ImportPythonModule(module_name)
  if not module_object:
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
        maximum_version=version_tuple[2], verbose_output=verbose_output):
      check_result = False

  if not _CheckSQLite3(verbose_output=verbose_output):
    check_result = False

  if check_result and not verbose_output:
    print(u'[OK]')

  print(u'')
  return check_result


def CheckModuleVersion(module_name):
  """Checks the version requirements of a module.

  Args:
    module_name (str): name of the module.

  Raises:
    ImportError: if the module does not exists or does not meet
                 the version requirements.
  """
  try:
    module_object = list(map(__import__, [module_name]))[0]
  except ImportError:
    raise

  if module_name not in PYTHON_DEPENDENCIES:
    return

  version_attribute_name, minimum_version, maximum_version = (
      PYTHON_DEPENDENCIES[module_name])

  module_version = None
  if not version_attribute_name.endswith(u'()'):
    module_version = getattr(module_object, version_attribute_name, None)
  else:
    version_method = getattr(module_object, version_attribute_name[:-2], None)
    if version_method:
      module_version = version_method()

  if not module_version:
    raise ImportError(u'Unable to determine version of module: {0:s}'.format(
        module_name))

  # Split the version string and convert every digit into an integer.
  # A string compare of both version strings will yield an incorrect result.
  module_version_map = list(
      map(int, _VERSION_SPLIT_REGEX.split(module_version)))
  minimum_version_map = list(
      map(int, _VERSION_SPLIT_REGEX.split(minimum_version)))

  if module_version_map < minimum_version_map:
    raise ImportError((
        u'Module: {0:s} version: {1!s} is too old, {2!s} or later '
        u'required.').format(module_name, module_version, minimum_version))

  if maximum_version:
    maximum_version_map = list(
        map(int, _VERSION_SPLIT_REGEX.split(maximum_version)))
    if module_version_map > maximum_version_map:
      raise ImportError((
          u'Module; {0:s} version: {1!s} is too recent, {2!s} or earlier '
          u'required.').format(module_name, module_version, maximum_version))


def CheckTestDependencies():
  """Checks the availability of the dependencies when running tests.

  Returns:
    bool: True if the dependencies are available, False otherwise.
  """
  if not CheckDependencies():
    return False

  print(u'Checking availability and versions of test dependencies.')
  for module_name, version_tuple in sorted(PYTHON_DEPENDENCIES.items()):
    if not _CheckPythonModule(
        module_name, version_tuple[0], version_tuple[1],
        maximum_version=version_tuple[2]):
      return False

  return True


def GetDPKGDepends(exclude_version=False):
  """Retrieves the DPKG control file installation requirements.

  Args:
    exclude_version (Optional[bool]): True if the version should be excluded
        from the dependency definitions.

  Returns:
    list[str]: dependency definitions for requires for DPKG control file.
  """
  requires = []
  for module_name, version_tuple in sorted(PYTHON_DEPENDENCIES.items()):
    module_version = version_tuple[1]

    # Map the import name to the DPKG package name.
    module_name = _DPKG_PACKAGE_NAMES.get(
        module_name, u'python-{0:s}'.format(module_name))
    if module_name == u'python-libs':
      # Override the python-libs version since it does not match
      # the sqlite3 version.
      module_version = None

    if exclude_version or not module_version:
      requires.append(module_name)
    else:
      requires.append(u'{0:s} (>= {1!s})'.format(module_name, module_version))

  return sorted(requires)


def GetInstallRequires():
  """Retrieves the setup.py installation requirements.

  Returns:
    list[str]: dependency definitions for install_requires for setup.py.
  """
  install_requires = []
  for module_name, version_tuple in sorted(PYTHON_DEPENDENCIES.items()):
    module_version = version_tuple[1]
    maximum_version = version_tuple[2]

    # Map the import name to the PyPI project name.
    module_name = _PYPI_PROJECT_NAMES.get(module_name, module_name)
    if module_name == u'efilter':
      module_version = u'1-{0:s}'.format(module_version)

    elif module_name == u'pysqlite':
      # Override the pysqlite version since it does not match
      # the sqlite3 version.
      module_version = None

    if not module_version:
      install_requires.append(module_name)
    elif not maximum_version:
      install_requires.append(u'{0:s} >= {1!s}'.format(
          module_name, module_version))
    else:
      install_requires.append(u'{0:s} >= {1!s},<= {2!s}'.format(
          module_name, module_version, maximum_version))

  return sorted(install_requires)


def GetRPMRequires():
  """Retrieves the setup.cfg RPM installation requirements.

  Returns:
    list[str]: dependency definitions for requires for setup.cfg.
  """
  requires = []
  for module_name, version_tuple in sorted(PYTHON_DEPENDENCIES.items()):
    module_version = version_tuple[1]

    # Map the import name to the RPM package name.
    module_name = _RPM_PACKAGE_NAMES.get(
        module_name, u'python-{0:s}'.format(module_name))
    if module_name == u'python-libs':
      # Override the python-libs version since it does not match
      # the sqlite3 version.
      module_version = None

    if not module_version:
      requires.append(module_name)
    else:
      requires.append(u'{0:s} >= {1!s}'.format(module_name, module_version))

  return sorted(requires)
