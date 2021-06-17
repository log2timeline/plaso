# -*- coding: utf-8 -*-
"""CLI related functions and classes for testing."""

import argparse
import io
import operator
import os
import sys

from plaso.cli import tools

from tests import test_lib as shared_test_lib


if sys.version_info >= (3, 10):
  ARGPARSE_OPTIONS = 'options'
else:
  ARGPARSE_OPTIONS = 'optional arguments'


class SortedArgumentsHelpFormatter(argparse.HelpFormatter):
  """Class that implements an argparse help formatter with sorted arguments."""

  def add_arguments(self, actions):
    """Adds arguments.

    Args:
      actions (list[argparse._StoreAction]): command line actions.
    """
    actions = sorted(actions, key=operator.attrgetter('option_strings'))
    super(SortedArgumentsHelpFormatter, self).add_arguments(actions)


class TestOptions(object):
  """Class to define test options."""


class TestOutputWriter(tools.FileObjectOutputWriter):
  """Test output writer that reads and writes strings."""

  def __init__(self, encoding='utf-8'):
    """Initializes the output writer object.

    Args:
      encoding (Optional[str]): output encoding.
    """
    file_object = io.StringIO()
    super(TestOutputWriter, self).__init__(file_object, encoding=encoding)
    self._read_offset = 0

  def Write(self, string):
    """Writes a string to the output.

    Args:
      string (str): output.
    """
    # To mimic the behavior of the parent FileObjectOutputWriter, we encode the
    # provided string into the specified encoding, replacing invalid characters.
    byte_stream = string.encode(self._encoding, errors='replace')
    string = byte_stream.decode(self._encoding, errors='strict')

    self._file_object.write(string)

  def ReadOutput(self):
    """Reads all output added since the last call to ReadOutput.

    Returns:
      str: output data.
    """
    self._file_object.seek(self._read_offset, os.SEEK_SET)
    output_data = self._file_object.read()
    self._read_offset = self._file_object.tell()

    return output_data


class TestBinaryOutputWriter(tools.FileObjectOutputWriter):
  """Test output writer that reads and writes bytes."""

  def __init__(self, encoding='utf-8'):
    """Initializes the output writer object.

    Args:
      encoding (Optional[str]): output encoding.
    """
    file_object = io.BytesIO()
    super(TestBinaryOutputWriter, self).__init__(file_object, encoding=encoding)
    self._read_offset = 0

  def ReadOutput(self):
    """Reads all output added since the last call to ReadOutput.

    Returns:
      bytes: output data.
    """
    self._file_object.seek(self._read_offset, os.SEEK_SET)
    output_data = self._file_object.read()
    self._read_offset = self._file_object.tell()

    return output_data


class CLIToolTestCase(shared_test_lib.BaseTestCase):
  """The unit test case for a CLI tool."""

  def _RunArgparseFormatHelp(self, argument_parser):
    """Runs argparse.format_help() with test conditions.

    Args:
      argument_parser (argparse.ArgumentParser): argument parser.

    Returns:
      bytes: output of argparse.format_help().
    """
    columns_environment_variable = os.environ.get('COLUMNS', None)
    os.environ['COLUMNS'] = '80'

    try:
      output = argument_parser.format_help()
    finally:
      if columns_environment_variable:
        os.environ['COLUMNS'] = columns_environment_variable
      else:
        del os.environ['COLUMNS']

    return output
