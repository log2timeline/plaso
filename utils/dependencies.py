# -*- coding: utf-8 -*-
"""Helper to check for availability and version of dependencies."""

from __future__ import print_function
import re

try:
  import ConfigParser as configparser
except ImportError:
  import configparser  # pylint: disable=import-error


class DependencyDefinition(object):
  """Dependency definition.

  Attributes:
    dpkg_name (str): name of the dpkg package that provides the dependency.
    is_optional (bool): True if the dependency is optional.
    l2tbinaries_name (str): name of the l2tbinaries package that provides
        the dependency.
    maximum_version (str): maximum supported version.
    minimum_version (str): minimum supported version.
    name (str): name of (the Python module that provides) the dependency.
    pypi_name (str): name of the PyPI package that provides the dependency.
    python2_only (bool): True if the dependency is only supported by Python 2.
    rpm_name (str): name of the rpm package that provides the dependency.
    version_property (str): name of the version attribute or function.
  """

  def __init__(self, name):
    """Initializes a dependency configuation.

    Args:
      name (str): name of the dependency.
    """
    super(DependencyDefinition, self).__init__()
    self.dpkg_name = None
    self.is_optional = False
    self.l2tbinaries_name = None
    self.maximum_version = None
    self.minimum_version = None
    self.name = name
    self.pypi_name = None
    self.python2_only = False
    self.rpm_name = None
    self.version_property = None


class DependencyDefinitionReader(object):
  """Dependency definition reader."""

  _VALUE_NAMES = frozenset([
      u'dpkg_name',
      u'is_optional',
      u'l2tbinaries_name',
      u'maximum_version',
      u'minimum_version',
      u'pypi_name',
      u'python2_only',
      u'rpm_name',
      u'version_property'])

  def _GetConfigValue(self, config_parser, section_name, value_name):
    """Retrieves a value from the config parser.

    Args:
      config_parser (ConfigParser): configuration parser.
      section_name (str): name of the section that contains the value.
      value_name (str): name of the value.

    Returns:
      object: configuration value or None if the value does not exists.
    """
    try:
      return config_parser.get(section_name, value_name)
    except configparser.NoOptionError:
      return

  def Read(self, file_object):
    """Reads dependency definitions.

    Args:
      file_object (file): file-like object to read from.

    Yields:
      DependencyDefinition: dependency definition.
    """
    config_parser = configparser.RawConfigParser()
    config_parser.readfp(file_object)

    for section_name in config_parser.sections():
      dependency_definition = DependencyDefinition(section_name)
      for value_name in self._VALUE_NAMES:
        value = self._GetConfigValue(config_parser, section_name, value_name)
        setattr(dependency_definition, value_name, value)

      yield dependency_definition


class DependencyHelper(object):
  """Dependency helper."""

  _VERSION_SPLIT_REGEX = re.compile(r'\.|\-')

  def __init__(self):
    """Initializes a dependency helper."""
    super(DependencyHelper, self).__init__()
    self._dependencies = {}
    self._test_dependencies = {}

    dependency_reader = DependencyDefinitionReader()

    with open(u'dependencies.ini', 'r') as file_object:
      for dependency in dependency_reader.Read(file_object):
        self._dependencies[dependency.name] = dependency

    dependency = DependencyDefinition(u'mock')
    dependency.minimum_version = u'0.7.1'
    dependency.version_property = u'__version__'
    self._test_dependencies[u'mock'] = dependency

  def _CheckPythonModule(self, dependency):
    """Checks the availability of a Python module.

    Args:
      dependency (DependencyDefinition): dependency definition.

    Returns:
      tuple: consists:

        bool: True if the Python module is available and conforms to
            the minimum required version, False otherwise.
        str: status message.
    """
    module_object = self._ImportPythonModule(dependency.name)
    if not module_object:
      status_message = u'missing: {0:s}'.format(dependency.name)
      return dependency.is_optional, status_message

    if not dependency.version_property or not dependency.minimum_version:
      return True, dependency.name

    return self._CheckPythonModuleVersion(
        dependency.name, module_object, dependency.version_property,
        dependency.minimum_version, dependency.maximum_version)

  def _CheckPythonModuleVersion(
      self, module_name, module_object, version_property, minimum_version,
      maximum_version):
    """Checks the version of a Python module.

    Args:
      module_object (module): Python module.
      module_name (str): name of the Python module.
      version_property (str): version attribute or function.
      minimum_version (str): minimum version.
      maximum_version (str): maximum version.

    Returns:
      tuple: consists:

        bool: True if the Python module is available and conforms to
            the minimum required version, False otherwise.
        str: status message.
    """
    module_version = None
    if not version_property.endswith(u'()'):
      module_version = getattr(module_object, version_property, None)
    else:
      version_method = getattr(
          module_object, version_property[:-2], None)
      if version_method:
        module_version = version_method()

    if not module_version:
      status_message = (
          u'unable to determine version information for: {0:s}').format(
              module_name)
      return False, status_message

    # Make sure the module version is a string.
    module_version = u'{0!s}'.format(module_version)

    # Split the version string and convert every digit into an integer.
    # A string compare of both version strings will yield an incorrect result.
    module_version_map = list(
        map(int, self._VERSION_SPLIT_REGEX.split(module_version)))
    minimum_version_map = list(
        map(int, self._VERSION_SPLIT_REGEX.split(minimum_version)))

    if module_version_map < minimum_version_map:
      status_message = (
          u'{0:s} version: {1!s} is too old, {2!s} or later required').format(
              module_name, module_version, minimum_version)
      return False, status_message

    if maximum_version:
      maximum_version_map = list(
          map(int, self._VERSION_SPLIT_REGEX.split(maximum_version)))
      if module_version_map > maximum_version_map:
        status_message = (
            u'{0:s} version: {1!s} is too recent, {2!s} or earlier '
            u'required').format(module_name, module_version, maximum_version)
        return False, status_message

    status_message = u'{0:s} version: {1!s}'.format(module_name, module_version)
    return True, status_message

  def _CheckSQLite3(self):
    """Checks the availability of sqlite3.

    Returns:
      tuple: consists:

        bool: True if the Python module is available and conforms to
            the minimum required version, False otherwise.
        str: status message.
    """
    # On Windows sqlite3 can be provided by both pysqlite2.dbapi2 and
    # sqlite3. sqlite3 is provided with the Python installation and
    # pysqlite2.dbapi2 by the pysqlite2 Python module. Typically
    # pysqlite2.dbapi2 would contain a newer version of sqlite3, hence
    # we check for its presence first.
    module_name = u'pysqlite2.dbapi2'
    minimum_version = u'3.7.8'

    module_object = self._ImportPythonModule(module_name)
    if not module_object:
      module_name = u'sqlite3'

    module_object = self._ImportPythonModule(module_name)
    if not module_object:
      status_message = u'missing: {0:s}.'.format(module_name)
      return False, status_message

    return self._CheckPythonModuleVersion(
        module_name, module_object, u'sqlite_version', minimum_version, None)

  def _ImportPythonModule(self, module_name):
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

  def _PrintCheckDependencyStatus(
      self, dependency, result, status_message, verbose_output=True):
    """Prints the check dependency status.

    Args:
      dependency (DependencyDefinition): dependency definition.
      result (bool): True if the Python module is available and conforms to
            the minimum required version, False otherwise.
      status_message (str): status message.
    """
    if not result or dependency.is_optional:
      if dependency.is_optional:
        status_indicator = u'[OPTIONAL]'
      else:
        status_indicator = u'[FAILURE]'

      print(u'{0:s}\t{1:s}.'.format(status_indicator, status_message))

    elif verbose_output:
      print(u'[OK]\t\t{0:s}'.format(status_message))

  def CheckDependencies(self, verbose_output=True):
    """Checks the availability of the dependencies.

    Args:
      verbose_output (Optional[bool]): True if output should be verbose.

    Returns:
      bool: True if the dependencies are available, False otherwise.
    """
    print(u'Checking availability and versions of dependencies.')
    check_result = True

    for module_name, dependency in sorted(self._dependencies.items()):
      if module_name == u'sqlite3':
        result, status_message = self._CheckSQLite3()
      else:
        result, status_message = self._CheckPythonModule(dependency)

      if not result:
        check_result = False

      self._PrintCheckDependencyStatus(
          dependency, result, status_message, verbose_output=verbose_output)

    if check_result and not verbose_output:
      print(u'[OK]')

    print(u'')
    return check_result

  def CheckTestDependencies(self, verbose_output=True):
    """Checks the availability of the dependencies when running tests.

    Args:
      verbose_output (Optional[bool]): True if output should be verbose.

    Returns:
      bool: True if the dependencies are available, False otherwise.
    """
    if not self.CheckDependencies(verbose_output=verbose_output):
      return False

    print(u'Checking availability and versions of test dependencies.')
    check_result = True

    for dependency in sorted(
        self._test_dependencies.values(),
        key=lambda dependency: dependency.name):
      result, status_message = self._CheckPythonModule(dependency)
      if not result:
        check_result = False

      self._PrintCheckDependencyStatus(
          dependency, result, status_message, verbose_output=verbose_output)

    if check_result and not verbose_output:
      print(u'[OK]')

    print(u'')
    return check_result

  def GetDPKGDepends(self, exclude_version=False):
    """Retrieves the DPKG control file installation requirements.

    Args:
      exclude_version (Optional[bool]): True if the version should be excluded
          from the dependency definitions.

    Returns:
      list[str]: dependency definitions for requires for DPKG control file.
    """
    requires = []
    for dependency in sorted(
        self._dependencies.values(), key=lambda dependency: dependency.name):
      module_name = dependency.dpkg_name or dependency.name

      if exclude_version or not dependency.minimum_version:
        requires_string = module_name
      else:
        requires_string = u'{0:s} (>= {1:s})'.format(
            module_name, dependency.minimum_version)

      requires.append(requires_string)

    return sorted(requires)

  def GetL2TBinaries(self):
    """Retrieves the l2tbinaries requirements.

    Returns:
      list[str]: dependency definitions for l2tbinaries.
    """
    requires = []
    for dependency in sorted(
        self._dependencies.values(), key=lambda dependency: dependency.name):
      module_name = dependency.l2tbinaries_name or dependency.name

      requires.append(module_name)

    return sorted(requires)

  def GetInstallRequires(self):
    """Retrieves the setup.py installation requirements.

    Returns:
      list[str]: dependency definitions for install_requires for setup.py.
    """
    install_requires = []
    for dependency in sorted(
        self._dependencies.values(), key=lambda dependency: dependency.name):
      module_name = dependency.pypi_name or dependency.name

      if module_name == u'efilter':
        requires_string = u'{0:s} == 1-{1!s}'.format(
            module_name, dependency.minimum_version)
        install_requires.append(requires_string)
        continue

      # Use the sqlite3 module provided by the standard library.
      if module_name == u'pysqlite':
        continue

      if not dependency.minimum_version:
        requires_string = module_name
      elif not dependency.maximum_version:
        requires_string = u'{0:s} >= {1!s}'.format(
            module_name, dependency.minimum_version)
      else:
        requires_string = u'{0:s} >= {1!s},<= {2!s}'.format(
            module_name, dependency.minimum_version, dependency.maximum_version)

      if dependency.python2_only:
        requires_string = u'{0:s} ; python_version < \'3.0\''.format(
            requires_string)

      install_requires.append(requires_string)

    return sorted(install_requires)

  def GetRPMRequires(self, exclude_version=False):
    """Retrieves the setup.cfg RPM installation requirements.

    Args:
      exclude_version (Optional[bool]): True if the version should be excluded
          from the dependency definitions.

    Returns:
      list[str]: dependency definitions for requires for setup.cfg.
    """
    requires = []
    for dependency in sorted(
        self._dependencies.values(), key=lambda dependency: dependency.name):
      module_name = dependency.rpm_name or dependency.name

      if exclude_version or not dependency.minimum_version:
        requires_string = module_name
      else:
        requires_string = u'{0:s} >= {1:s}'.format(
            module_name, dependency.minimum_version)

      requires.append(requires_string)

    return sorted(requires)
