# -*- coding: utf-8 -*-
"""Helper to check for availability and version of dependencies."""

from __future__ import print_function
from __future__ import unicode_literals

import configparser
import re


class DependencyDefinition(object):
  """Dependency definition.

  Attributes:
    dpkg_name (str): name of the dpkg package that provides the dependency.
    is_optional (bool): True if the dependency is optional.
    l2tbinaries_macos_name (str): name of the l2tbinaries macos package that
        provides the dependency.
    l2tbinaries_name (str): name of the l2tbinaries package that provides
        the dependency.
    maximum_version (str): maximum supported version, a greater or equal
        version is not supported.
    minimum_version (str): minimum supported version, a lesser version is
        not supported.
    name (str): name of (the Python module that provides) the dependency.
    pypi_name (str): name of the PyPI package that provides the dependency.
    python2_only (bool): True if the dependency is only supported by Python 2.
    python3_only (bool): True if the dependency is only supported by Python 3.
    rpm_name (str): name of the rpm package that provides the dependency.
    skip_check (bool): True if the dependency should be skipped by the
        CheckDependencies or CheckTestDependencies methods of DependencyHelper.
    version_property (str): name of the version attribute or function.
  """

  def __init__(self, name):
    """Initializes a dependency configuration.

    Args:
      name (str): name of the dependency.
    """
    super(DependencyDefinition, self).__init__()
    self.dpkg_name = None
    self.is_optional = False
    self.l2tbinaries_macos_name = None
    self.l2tbinaries_name = None
    self.maximum_version = None
    self.minimum_version = None
    self.name = name
    self.pypi_name = None
    self.python2_only = False
    self.python3_only = False
    self.rpm_name = None
    self.skip_check = None
    self.version_property = None


class DependencyDefinitionReader(object):
  """Dependency definition reader."""

  _VALUE_NAMES = frozenset([
      'dpkg_name',
      'is_optional',
      'l2tbinaries_macos_name',
      'l2tbinaries_name',
      'maximum_version',
      'minimum_version',
      'pypi_name',
      'python2_only',
      'python3_only',
      'rpm_name',
      'skip_check',
      'version_property'])

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
      return None

  def Read(self, file_object):
    """Reads dependency definitions.

    Args:
      file_object (file): file-like object to read from.

    Yields:
      DependencyDefinition: dependency definition.
    """
    config_parser = configparser.ConfigParser(interpolation=None)
    config_parser.read_file(file_object)

    for section_name in config_parser.sections():
      dependency_definition = DependencyDefinition(section_name)
      for value_name in self._VALUE_NAMES:
        value = self._GetConfigValue(config_parser, section_name, value_name)
        setattr(dependency_definition, value_name, value)

      yield dependency_definition


class DependencyHelper(object):
  """Dependency helper.

  Attributes:
    dependencies (dict[str, DependencyDefinition]): dependencies.
  """

  _VERSION_NUMBERS_REGEX = re.compile(r'[0-9.]+')
  _VERSION_SPLIT_REGEX = re.compile(r'\.|\-')

  def __init__(self, configuration_file='dependencies.ini'):
    """Initializes a dependency helper.

    Args:
      configuration_file (Optional[str]): path to the dependencies
          configuration file.
    """
    super(DependencyHelper, self).__init__()
    self._test_dependencies = {}
    self.dependencies = {}

    dependency_reader = DependencyDefinitionReader()

    with open(configuration_file, 'r') as file_object:
      for dependency in dependency_reader.Read(file_object):
        self.dependencies[dependency.name] = dependency

    dependency = DependencyDefinition('mock')
    dependency.minimum_version = '0.7.1'
    dependency.version_property = '__version__'
    self._test_dependencies['mock'] = dependency

  def _CheckPythonModule(self, dependency):
    """Checks the availability of a Python module.

    Args:
      dependency (DependencyDefinition): dependency definition.

    Returns:
      tuple: containing:

        bool: True if the Python module is available and conforms to
            the minimum required version, False otherwise.
        str: status message.
    """
    module_object = self._ImportPythonModule(dependency.name)
    if not module_object:
      status_message = 'missing: {0:s}'.format(dependency.name)
      return False, status_message

    if not dependency.version_property:
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
      tuple: containing:

        bool: True if the Python module is available and conforms to
            the minimum required version, False otherwise.
        str: status message.
    """
    module_version = None
    if not version_property.endswith('()'):
      module_version = getattr(module_object, version_property, None)
    else:
      version_method = getattr(
          module_object, version_property[:-2], None)
      if version_method:
        module_version = version_method()

    if not module_version:
      status_message = (
          'unable to determine version information for: {0:s}').format(
              module_name)
      return False, status_message

    # Make sure the module version is a string.
    module_version = '{0!s}'.format(module_version)

    # Split the version string and convert every digit into an integer.
    # A string compare of both version strings will yield an incorrect result.

    # Strip any semantic suffixes such as a1, b1, pre, post, rc, dev.
    module_version = self._VERSION_NUMBERS_REGEX.findall(module_version)[0]

    if module_version[-1] == '.':
      module_version = module_version[:-1]

    try:
      module_version_map = list(
          map(int, self._VERSION_SPLIT_REGEX.split(module_version)))
    except ValueError:
      status_message = 'unable to parse module version: {0:s} {1:s}'.format(
          module_name, module_version)
      return False, status_message

    if minimum_version:
      try:
        minimum_version_map = list(
            map(int, self._VERSION_SPLIT_REGEX.split(minimum_version)))
      except ValueError:
        status_message = 'unable to parse minimum version: {0:s} {1:s}'.format(
            module_name, minimum_version)
        return False, status_message

      if module_version_map < minimum_version_map:
        status_message = (
            '{0:s} version: {1!s} is too old, {2!s} or later required').format(
                module_name, module_version, minimum_version)
        return False, status_message

    if maximum_version:
      try:
        maximum_version_map = list(
            map(int, self._VERSION_SPLIT_REGEX.split(maximum_version)))
      except ValueError:
        status_message = 'unable to parse maximum version: {0:s} {1:s}'.format(
            module_name, maximum_version)
        return False, status_message

      if module_version_map > maximum_version_map:
        status_message = (
            '{0:s} version: {1!s} is too recent, {2!s} or earlier '
            'required').format(module_name, module_version, maximum_version)
        return False, status_message

    status_message = '{0:s} version: {1!s}'.format(module_name, module_version)
    return True, status_message

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
      return None

    # If the module name contains dots get the upper most module object.
    if '.' in module_name:
      for submodule_name in module_name.split('.')[1:]:
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
      verbose_output (Optional[bool]): True if output should be verbose.
    """
    if not result or dependency.is_optional:
      if dependency.is_optional:
        status_indicator = '[OPTIONAL]'
      else:
        status_indicator = '[FAILURE]'

      print('{0:s}\t{1:s}'.format(status_indicator, status_message))

    elif verbose_output:
      print('[OK]\t\t{0:s}'.format(status_message))

  def CheckDependencies(self, verbose_output=True):
    """Checks the availability of the dependencies.

    Args:
      verbose_output (Optional[bool]): True if output should be verbose.

    Returns:
      bool: True if the dependencies are available, False otherwise.
    """
    print('Checking availability and versions of dependencies.')
    check_result = True

    for _, dependency in sorted(self.dependencies.items()):
      if dependency.skip_check:
        continue

      result, status_message = self._CheckPythonModule(dependency)

      if not result and not dependency.is_optional:
        check_result = False

      self._PrintCheckDependencyStatus(
          dependency, result, status_message, verbose_output=verbose_output)

    if check_result and not verbose_output:
      print('[OK]')

    print('')
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

    print('Checking availability and versions of test dependencies.')
    check_result = True

    for dependency in sorted(
        self._test_dependencies.values(),
        key=lambda dependency: dependency.name):
      if dependency.skip_check:
        continue

      result, status_message = self._CheckPythonModule(dependency)
      if not result:
        check_result = False

      self._PrintCheckDependencyStatus(
          dependency, result, status_message, verbose_output=verbose_output)

    if check_result and not verbose_output:
      print('[OK]')

    print('')
    return check_result
