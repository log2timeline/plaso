# -*- coding: utf-8 -*-
"""The analysis CLI tool."""

import os

from plaso.cli import tools
from plaso.lib import errors


class AnalysisTool(tools.CLITool):
  """Class that implements an analysis CLI tool."""

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader: the input reader (instance of InputReader).
                    The default is None which indicates the use of the stdin
                    input reader.
      output_writer: the output writer (instance of OutputWriter).
                     The default is None which indicates the use of the stdout
                     output writer.
    """
    super(AnalysisTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._storage_file_path = None

  def _ParseStorageFileOptions(self, options):
    """Parses the storage file options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._storage_file_path = getattr(options, u'storage_file', None)
    if not self._storage_file_path:
      raise errors.BadConfigOption(u'Missing storage file option.')

    if not os.path.isfile(self._storage_file_path):
      raise errors.BadConfigOption(
          u'No such storage file: {0:s}.'.format(self._storage_file_path))

  def AddStorageFileOptions(self, argument_group):
    """Adds the storage file options to the argument group.

    Args:
      argument_group: the argparse argument group (instance of
                      argparse._ArgumentGroup) or argument parser (instance of
                      argparse.ArgumentParser).
    """
    argument_group.add_argument(
        u'storage_file', metavar=u'STORAGE_FILE', nargs=u'?', type=unicode,
        default=None, help=u'The path of the storage file.')

  def ParseOptions(self, options):
    """Parses tool specific options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    super(AnalysisTool, self).ParseOptions(options)
    self._ParseStorageFileOptions(options)
