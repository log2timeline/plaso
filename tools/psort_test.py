#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the psort CLI tool."""

import os
import unittest

from plaso.cli.helpers import interface as helpers_interface
from plaso.cli.helpers import manager as helpers_manager
from plaso.lib import errors
from plaso.output import manager as output_manager
from tests import test_lib as shared_test_lib
from tests.cli import test_lib as cli_test_lib
from tests.frontend import psort as psort_test

from tools import psort
from tools import test_lib


class TestInputReader(object):
  """Test input reader."""

  def __init__(self):
    """Initialize the reader."""
    super(TestInputReader, self).__init__()
    self.read_called = False

  def Read(self):
    """Mock a read operation by user."""
    self.read_called = True
    return u'foobar'


class TestOutputModuleArgumentHelper(helpers_interface.ArgumentsHelper):
  """Test argument helper for the test output module."""

  NAME = u'test_missing'

  @classmethod
  def AddArguments(cls, argument_group):
    """Mock the add argument section."""
    pass

  @classmethod
  def ParseOptions(cls, options, output_module):
    """Provide a test parse options section."""
    if not isinstance(output_module, TestOutputModuleMissingParameters):
      raise errors.BadConfigObject((
          u'Output module is not an instance of '
          u'TestOutputModuleMissingParameters'))

    missing = getattr(options, u'missing', None)
    if missing:
      output_module.SetMissingValue(u'missing', missing)

    parameters = getattr(options, u'parameters', None)
    if parameters:
      output_module.SetMissingValue(u'parameters', parameters)


class TestOutputModuleMissingParameters(psort_test.TestOutputModule):
  """Test output module that is missing some parameters."""

  NAME = u'test_missing'

  # For test purpose assign these as class attributes.
  missing = None
  parameters = None

  def GetMissingArguments(self):
    """Return a list of missing parameters."""
    missing_parameters = []
    if self.missing is None:
      missing_parameters.append(u'missing')

    if self.parameters is None:
      missing_parameters.append(u'parameters')

    return missing_parameters

  @classmethod
  def SetMissingValue(cls, attribute, value):
    """Set missing value."""
    setattr(cls, attribute, value)


class PsortToolTest(test_lib.ToolTestCase):
  """Tests for the psort tool."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._input_reader = TestInputReader()
    self._output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')

    self._test_tool = psort.PsortTool(
        input_reader=self._input_reader, output_writer=self._output_writer)

  def testListOutputModules(self):
    """Test the listing of output modules."""
    self._test_tool.ListOutputModules()
    raw_data = self._output_writer.ReadOutput()

    # Since the printed output varies depending on which output modules are
    # enabled we cannot test the complete string but rather test substrings.
    self.assertTrue(raw_data.startswith((
        b'\n******************************** Output Modules '
        b'********************************')))

    for name, output_class in output_manager.OutputManager.GetOutputClasses():
      expected_string = u'{0:s} : {1:s}'.format(name, output_class.DESCRIPTION)
      self.assertTrue(expected_string in raw_data)

  def testProcessStorageWithMissingParameters(self):
    """Test the ProcessStorage function with half-configured output module."""
    options = cli_test_lib.TestOptions()
    options.storage_file = self._GetTestFilePath([u'psort_test.out'])
    options.output_format = u'test_missing'

    output_manager.OutputManager.RegisterOutput(
        TestOutputModuleMissingParameters)
    helpers_manager.ArgumentHelperManager.RegisterHelper(
        TestOutputModuleArgumentHelper)

    lines = []
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file_name = os.path.join(temp_directory, u'output.txt')
      options.write = temp_file_name

      self._test_tool.ParseOptions(options)
      self._test_tool.ProcessStorage()

      with open(temp_file_name, 'rb') as file_object:
        for line in file_object:
          lines.append(line.strip())

    self.assertTrue(self._input_reader.read_called)
    self.assertEqual(TestOutputModuleMissingParameters.missing, u'foobar')
    self.assertEqual(TestOutputModuleMissingParameters.parameters, u'foobar')

    self.assertIn(u'FILE/Unknown FS ctime OS:syslog', lines)
    output_manager.OutputManager.DeregisterOutput(
        TestOutputModuleMissingParameters)
    helpers_manager.ArgumentHelperManager.DeregisterHelper(
        TestOutputModuleArgumentHelper)


if __name__ == '__main__':
  unittest.main()
