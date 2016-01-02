#!/usr/bin/python
# -*- coding: utf-8 -*-
"""End-to-end test launcher."""

from __future__ import print_function
import abc
import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile

try:
  import ConfigParser as configparser
except ImportError:
  import configparser


# Since os.path.abspath() uses the current working directory (cwd)
# os.path.abspath(__file__) will point to a different location if
# cwd has been changed. Hence we preserve the absolute location of __file__.
__file__ = os.path.abspath(__file__)


class TempDirectory(object):
  """Class that implements a temporary directory."""

  def __init__(self):
    """Initializes a temporary directory object."""
    super(TempDirectory, self).__init__()
    self.name = u''

  def __enter__(self):
    """Make this work with the 'with' statement."""
    self.name = tempfile.mkdtemp()
    return self.name

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make this work with the 'with' statement."""
    shutil.rmtree(self.name, True)


class TestCase(object):
  """Class that defines the test case object interface.

  Attributes:
    name: a string containing the name of the test case.
  """

  NAME = None

  def __init__(self, tools_path, test_results_path, debug_output=False):
    """Initializes a test case object.

    Args:
      tools_path: a string containing the path to the plaso tools.
      test_results_path: a string containing the path to store test results.
      debug_output: optional boolean value to indicate that debug output
                    should be generated.
    """
    super(TestCase, self).__init__()
    self._debug_output = debug_output
    self._test_results_path = test_results_path
    self._tools_path = tools_path

  def _RunCommand(self, command):
    """Runs a command.

    Args:
      command: a string containing the command to run.

    Returns:
      A boolean indicating the command ran successfully.
    """
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    return True

  @abc.abstractmethod
  def ReadAttributes(self, test_definition_reader, test_definition):
    """Reads the test definition attributes.

    Args:
      test_definition_reader: a test definition reader object (instance of
                              TestDefinitionReader).
      test_definition: a test definition object (instance of TestDefinition).

    Returns:
      A boolean indicating the read was successful.
    """

  @abc.abstractmethod
  def Run(self, test_definition):
    """Runs the tests.

    Args:
      test_definition: a test definition object (instance of TestDefinition).

    Returns:
      A boolean value indicating the tests ran successfully.
    """


class TestCasesManager(object):
  """Class that implements the test cases manager."""

  _test_case_classes = {}
  _test_case_objects = {}

  @classmethod
  def DeregisterTestCase(cls, test_case_class):
    """Deregisters a test case class.

    The test case classes are identified based on their lower case name.

    Args:
      test_case_class: a class object of the test case.

    Raises:
      KeyError: if test case class is not set for the corresponding name.
    """
    test_case_name = test_case_class.NAME.lower()
    if test_case_name not in cls._test_case_classes:
      raise KeyError(
          u'Formatter class not set for name: {0:s}.'.format(
              test_case_class.NAME))

    del cls._test_case_classes[test_case_name]

  @classmethod
  def GetTestCaseObject(
      cls, name, tools_path, test_results_path, debug_output=False):
    """Retrieves the test case object for a specific name.

    Args:
      name: a string containing the name of the test case.
      tools_path: a string containing the path to the plaso tools.
      test_results_path: a string containing the path to store test results.
      debug_output: optional boolean value to indicate that debug output
                    should be generated.

    Returns:
      The corresponding test case (instance of TestCase) or
      None if not available.
    """
    name = name.lower()
    if name not in cls._test_case_objects:
      test_case_object = None

      if name in cls._test_case_classes:
        test_case_class = cls._test_case_classes[name]
        test_case_object = test_case_class(
            tools_path, test_results_path, debug_output=debug_output)

      if not test_case_object:
        return

      cls._test_case_objects[name] = test_case_object

    return cls._test_case_objects[name]

  @classmethod
  def RegisterTestCase(cls, test_case_class):
    """Registers a test case class.

    The test case classes are identified based on their lower case name.

    Args:
      test_case_class: a class object of the test case.

    Raises:
      KeyError: if test case class is already set for the corresponding
                name.
    """
    test_case_name = test_case_class.NAME.lower()
    if test_case_name in cls._test_case_classes:
      raise KeyError((
          u'Formatter class already set for name: {0:s}.').format(
              test_case_class.NAME))

    cls._test_case_classes[test_case_name] = test_case_class

  @classmethod
  def RegisterTestCases(cls, test_case_classes):
    """Registers test case classes.

    The test case classes are identified based on their lower case name.

    Args:
      test_case_classes: a list of class objects of the test cases.

    Raises:
      KeyError: if test case class is already set for the corresponding
                name.
    """
    for test_case_class in test_case_classes:
      cls.RegisterTestCase(test_case_class)


class TestDefinition(object):
  """Class that implements a test definition.

  Attributes:
    case: a string containing the name of test case.
    name: a string containing the name of the test.
  """

  def __init__(self, name):
    """Initializes a test definition object.

    Args:
      name: a string containing the name of the test.
    """
    super(TestDefinition, self).__init__()
    self.case = u''
    self.name = name


class TestDefinitionReader(object):
  """Class that implements a test definition reader."""

  def __init__(self, tools_path, test_results_path, debug_output=False):
    """Initializes a test definition reader object.

    Args:
      tools_path: a string containing the path to the plaso tools.
      test_results_path: a string containing the path to store test results.
      debug_output: optional boolean value to indicate that debug output
                    should be generated.
    """
    super(TestDefinitionReader, self).__init__()
    self._config_parser = None
    self._debug_output = debug_output
    self._test_results_path = test_results_path
    self._tools_path = tools_path

  def GetConfigValue(self, section_name, value_name):
    """Retrieves a value from the config parser.

    Args:
      section_name: a string containing the name of the section that
                    contains the value.
      value_name: a string of the name of the value.

    Returns:
      An object containing the value or None if the value does not exists.

    Raises:
      RuntimeError: if the configuration parser is not set.
    """
    if not self._config_parser:
      raise RuntimeError(u'Missing configuration parser.')

    try:
      return self._config_parser.get(section_name, value_name).decode('utf-8')
    except configparser.NoOptionError:
      return

  def Read(self, file_object):
    """Reads test definitions.

    Args:
      file_object: a file-like object to read from.

    Yields:
      End-to-end test definitions (instances of TestDefinition).
    """
    # TODO: replace by:
    # self._config_parser = configparser. ConfigParser(interpolation=None)
    self._config_parser = configparser.RawConfigParser()

    try:
      self._config_parser.readfp(file_object)

      for section_name in self._config_parser.sections():
        test_definition = TestDefinition(section_name)

        test_definition.case = self.GetConfigValue(section_name, u'case')
        if not test_definition.case:
          logging.warning(
              u'Test case missing in test definition: {0:s}.'.format(
                  section_name))
          continue

        test_case = TestCasesManager.GetTestCaseObject(
            test_definition.case, self._tools_path, self._test_results_path,
            debug_output=self._debug_output)
        if not test_case:
          logging.warning(u'Undefined test case: {0:s}'.format(
              test_definition.case))
          continue

        if not test_case.ReadAttributes(self, test_definition):
          logging.warning(
              u'Unable to read attributes of test case: {0:s}'.format(
                  test_definition.case))
          continue

        yield test_definition

    finally:
      self._config_parser = None


class TestLauncher(object):
  """Class that implements the test launcher."""

  def __init__(self, tools_path, test_results_path, debug_output=False):
    """Initializes a test launcher object.

    Args:
      tools_path: a string containing the path to the plaso tools.
      test_results_path: a string containing the path to store test results.
      debug_output: optional boolean value to indicate that debug output
                    should be generated.
    """
    super(TestLauncher, self).__init__()
    self._debug_output = debug_output
    self._test_definitions = []
    self._test_results_path = test_results_path
    self._tools_path = tools_path

  def _RunTest(self, test_definition):
    """Runs the test.

    Args:
      test_definition: a test definition object (instance of TestDefinition).

    Returns:
      A boolean value indicating the test ran successfully.
    """
    test_case = TestCasesManager.GetTestCaseObject(
        test_definition.case, self._tools_path, self._test_results_path)
    if not test_case:
      logging.error(u'Unsupported test case: {0:s}'.format(
          test_definition.case))
      return False

    return test_case.Run(test_definition)

  def ReadDefinitions(self, configuration_file):
    """Reads the test definitions from the configuration file.

    Args:
      configuration_file: a string containing the path of the configuration
                          file.
    """
    self._test_definitions = []
    with open(configuration_file) as file_object:
      test_definition_reader = TestDefinitionReader(
          self._tools_path, self._test_results_path)
      for test_definition in test_definition_reader.Read(file_object):
        self._test_definitions.append(test_definition)

  def RunTests(self):
    """Runs the tests.

    Returns:
      A list of strings containing the names of the failed tests.
    """
    # TODO: set up test environment

    failed_tests = []
    for test_definition in self._test_definitions:
      if not self._RunTest(test_definition):
        failed_tests.append(test_definition.name)

    return failed_tests


class ExtractAndOutputTestCase(TestCase):
  """Class that implements the extract and output test case."""

  NAME = u'extract_and_output'

  def __init__(self, tools_path, test_results_path):
    """Initializes a test case object.

    Args:
      tools_path: a string containing the path to the plaso tools.
      test_results_path: a string containing the path to store test results.
    """
    super(ExtractAndOutputTestCase, self).__init__(
        tools_path, test_results_path)
    self._log2timeline_path = None
    self._pinfo_path = None
    self._psort_path = None

    for filename in (
        u'log2timeline.exe', u'log2timeline.sh', u'log2timeline.py'):
      self._log2timeline_path = os.path.join(tools_path, filename)
      if os.path.exists(self._log2timeline_path):
        break

    if self._log2timeline_path.endswith(u'.py'):
      self._log2timeline_path = u' '.join([
          sys.executable, self._log2timeline_path])

    for filename in (u'pinfo.exe', u'pinfo.sh', u'pinfo.py'):
      self._pinfo_path = os.path.join(tools_path, filename)
      if os.path.exists(self._pinfo_path):
        break

    if self._pinfo_path.endswith(u'.py'):
      self._pinfo_path = u' '.join([sys.executable, self._pinfo_path])

    for filename in (u'psort.exe', u'psort.sh', u'psort.py'):
      self._psort_path = os.path.join(tools_path, filename)
      if os.path.exists(self._psort_path):
        break

    if self._psort_path.endswith(u'.py'):
      self._psort_path = u' '.join([sys.executable, self._psort_path])

  def ReadAttributes(self, test_definition_reader, test_definition):
    """Reads the test definition attributes.

    Args:
      test_definition_reader: a test definition reader object (instance of
                              TestDefinitionReader).
      test_definition: a test definition object (instance of TestDefinition).

    Returns:
      A boolean indicating the read was successful.
    """
    test_definition.extract_options = test_definition_reader.GetConfigValue(
        test_definition.name, u'extract_options')

    if test_definition.extract_options is None:
      test_definition.extract_options = []
    elif isinstance(test_definition.extract_options, basestring):
      test_definition.extract_options = test_definition.extract_options.split(
          u',')

    test_definition.source = test_definition_reader.GetConfigValue(
        test_definition.name, u'source')

    return True

  def Run(self, test_definition):
    """Runs the tests.

    Args:
      test_definition: a test definition object (instance of TestDefinition).

    Returns:
      A boolean value indicating the tests ran successfully.
    """
    if not os.path.exists(test_definition.source):
      logging.error(u'No such source: {0:s}'.format(test_definition.source))
      return False

    with TempDirectory() as temp_directory:
      storage_file = os.path.join(
          temp_directory, u'{0:s}.plaso'.format(test_definition.name))

      # Extract events with log2timeline.
      extract_options = u'--status-view=none {0:s}'.format(
          u' '.join(test_definition.extract_options))
      stdout_file = os.path.join(
          temp_directory, u'{0:s}-log2timeline.out'.format(
              test_definition.name))
      stderr_file = os.path.join(
          temp_directory, u'{0:s}-log2timeline.err'.format(
              test_definition.name))
      command = (
          u'{0:s} {1:s} {2:s} {3:s} > {4:s} 2> {5:s}').format(
              self._log2timeline_path, extract_options, storage_file,
              test_definition.source, stdout_file, stderr_file)

      logging.info(u'Running: {0:s}'.format(command))
      result = self._RunCommand(command)

      if self._debug_output:
        with open(stderr_file, 'rb') as file_object:
          output_data = file_object.read()
          print(output_data)

      if os.path.exists(storage_file):
        shutil.copy(storage_file, self._test_results_path)

      if os.path.exists(stdout_file):
        shutil.copy(stdout_file, self._test_results_path)
      if os.path.exists(stderr_file):
        shutil.copy(stderr_file, self._test_results_path)

      if not result:
        return False

      # Check if the resulting storage file can be opened with pinfo.
      stdout_file = os.path.join(
          temp_directory, u'{0:s}-pinfo.out'.format(
              test_definition.name))
      stderr_file = os.path.join(
          temp_directory, u'{0:s}-pinfo.err'.format(
              test_definition.name))
      command = (
          u'{0:s} {1:s} > {2:s} 2> {3:s}').format(
              self._pinfo_path, storage_file, stdout_file, stderr_file)

      logging.info(u'Running: {0:s}'.format(command))
      result = self._RunCommand(command)

      if self._debug_output:
        with open(stderr_file, 'rb') as file_object:
          output_data = file_object.read()
          print(output_data)

      if os.path.exists(stdout_file):
        shutil.copy(stdout_file, self._test_results_path)
      if os.path.exists(stderr_file):
        shutil.copy(stderr_file, self._test_results_path)

      if not result:
        return False

      # TODO: add support to compare storage file with a reference file.

      # Check if the resulting storage file can be opened with psort.
      stdout_file = os.path.join(
          temp_directory, u'{0:s}-psort.out'.format(
              test_definition.name))
      stderr_file = os.path.join(
          temp_directory, u'{0:s}-psort.err'.format(
              test_definition.name))
      command = (
          u'{0:s} {1:s} > {2:s} 2> {3:s}').format(
              self._psort_path, storage_file, stdout_file, stderr_file)

      logging.info(u'Running: {0:s}'.format(command))
      result = self._RunCommand(command)

      if self._debug_output:
        with open(stderr_file, 'rb') as file_object:
          output_data = file_object.read()
          print(output_data)

      if os.path.exists(stdout_file):
        shutil.copy(stdout_file, self._test_results_path)
      if os.path.exists(stderr_file):
        shutil.copy(stderr_file, self._test_results_path)

      if not result:
        return False

    return True


class OutputTestCase(TestCase):
  """Class that implements the output test case."""

  NAME = u'output'

  def __init__(self, tools_path, test_results_path):
    """Initializes a test case object.

    Args:
      tools_path: a string containing the path to the plaso tools.
      test_results_path: a string containing the path to store test results.
    """
    super(OutputTestCase, self).__init__(tools_path, test_results_path)
    self._psort_path = None

    for filename in (u'psort.exe', u'psort.sh', u'psort.py'):
      self._psort_path = os.path.join(tools_path, filename)
      if os.path.exists(self._psort_path):
        break

    if self._psort_path.endswith(u'.py'):
      self._psort_path = u' '.join([sys.executable, self._psort_path])

  def ReadAttributes(self, test_definition_reader, test_definition):
    """Reads the test definition attributes.

    Args:
      test_definition_reader: a test definition reader object (instance of
                              TestDefinitionReader).
      test_definition: a test definition object (instance of TestDefinition).

    Returns:
      A boolean indicating the read was successful.
    """
    test_definition.output_options = test_definition_reader.GetConfigValue(
        test_definition.name, u'output_options')

    if test_definition.output_options is None:
      test_definition.output_options = []
    elif isinstance(test_definition.output_options, basestring):
      test_definition.output_options = test_definition.output_options.split(
          u',')

    test_definition.source = test_definition_reader.GetConfigValue(
        test_definition.name, u'source')

    return True

  def Run(self, test_definition):
    """Runs the tests.

    Args:
      test_definition: a test definition object (instance of TestDefinition).

    Returns:
      A boolean value indicating the tests ran successfully.
    """
    if not os.path.exists(test_definition.source):
      logging.error(u'No such source: {0:s}'.format(test_definition.source))
      return False

    with TempDirectory() as temp_directory:
      # Output events with psort.
      output_options = u' '.join(test_definition.output_options)
      stdout_file = os.path.join(
          temp_directory, u'{0:s}-psort.out'.format(
              test_definition.name))
      stderr_file = os.path.join(
          temp_directory, u'{0:s}-psort.err'.format(
              test_definition.name))
      command = (
          u'{0:s} {1:s} {2:s} > {3:s} 2> {4:s}').format(
              self._psort_path, output_options, test_definition.source,
              stdout_file, stderr_file)

      logging.info(u'Running: {0:s}'.format(command))
      result = self._RunCommand(command)

      if self._debug_output:
        with open(stderr_file, 'rb') as file_object:
          output_data = file_object.read()
          print(output_data)

      if os.path.exists(stdout_file):
        shutil.copy(stdout_file, self._test_results_path)
      if os.path.exists(stderr_file):
        shutil.copy(stderr_file, self._test_results_path)

      if not result:
        return False

    return True


TestCasesManager.RegisterTestCases([
    ExtractAndOutputTestCase, OutputTestCase])


def Main():
  """The main function."""
  argument_parser = argparse.ArgumentParser(
      description=u'End-to-end test launcher.', add_help=False,
      formatter_class=argparse.RawDescriptionHelpFormatter)

  argument_parser.add_argument(
      u'-c', u'--config', dest=u'config_file', action=u'store',
      metavar=u'CONFIG_FILE', default=None,
      help=u'path of the test configuration file.')

  argument_parser.add_argument(
      u'--debug', dest=u'debug_output', action=u'store_true', default=False,
      help=u'enable debug output.')

  argument_parser.add_argument(
      u'--tools-directory', u'--tools_directory', action=u'store',
      metavar=u'DIRECTORY', dest=u'tools_directory', type=unicode,
      default=None, help=u'The location of the plaso tools directory.')

  argument_parser.add_argument(
      u'--results-directory', u'--results_directory', action=u'store',
      metavar=u'DIRECTORY', dest=u'results_directory', type=unicode,
      default=None, help=(
          u'The location o the directory where to store the test results.'))

  options = argument_parser.parse_args()

  if not options.config_file:
    options.config_file = os.path.dirname(__file__)
    options.config_file = os.path.dirname(options.config_file)
    options.config_file = os.path.join(
        options.config_file, u'config', u'end-to-end.ini')

  if not os.path.exists(options.config_file):
    print(u'No such config file: {0:s}.'.format(options.config_file))
    print(u'')
    return False

  logging.basicConfig(
      format=u'[%(levelname)s] %(message)s', level=logging.INFO)

  tools_path = options.tools_directory
  if not tools_path:
    tools_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), u'tools')

  test_results_path = options.results_directory
  if not test_results_path:
    test_results_path = os.getcwd()

  if not os.path.isdir(test_results_path):
    print(u'No such results directory: {0:s}.'.format(test_results_path))
    print(u'')
    return False

  tests = []
  with open(options.config_file) as file_object:
    test_definition_reader = TestDefinitionReader(
        tools_path, test_results_path, debug_output=options.debug_output)
    for test_definition in test_definition_reader.Read(file_object):
      tests.append(test_definition)

  test_launcher = TestLauncher(
      tools_path, test_results_path, debug_output=options.debug_output)
  test_launcher.ReadDefinitions(options.config_file)

  failed_tests = test_launcher.RunTests()
  if failed_tests:
    print(u'Failed tests:')
    for failed_test in failed_tests:
      print(u' {0:s}'.format(failed_test))

    print(u'')
    return False

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
