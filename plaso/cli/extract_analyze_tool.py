# -*- coding: utf-8 -*-
"""The extraction and analysis CLI tool."""

import datetime
import os

from plaso.cli import storage_media_tool
from plaso.lib import errors
from plaso.parsers import manager as parsers_manager


class ExtractionAndAnalysisTool(storage_media_tool.StorageMediaTool):
  """Class that implements a combined extraction and analysis CLI tool."""

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader (InputReader): the input reader, where None represents stdin.
      output_writer (OutputWriter): the output writer, where None represents
          stdout.
    """
    super(ExtractionAndAnalysisTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._parsers_manager = parsers_manager.ParsersManager
    self._storage_file_path = None

  def _GenerateStorageFileName(self):
    """Generates a name for the storage file.

    The result use a timestamp and the basename of the source path.

    Raises:
      BadConfigOption: raised if the source path is not set.
    """
    if not self._source_path:
      raise errors.BadConfigOption(u'Please define a source (--source).')

    timestamp = datetime.datetime.now()
    datetime_string = timestamp.strftime(u'%Y%m%dT%H%M%S')

    source_path = os.path.abspath(self._source_path)
    source_name = os.path.basename(source_path)

    if source_path.endswith(os.path.sep):
      source_path = os.path.dirname(source_path)

    source_name = os.path.basename(source_path)

    if not source_name or source_name in (u'/', u'\\'):
      # The user passed the filesystem's root as source
      source_name = u'ROOT'

    return u'{0:s}-{1:s}.plaso'.format(datetime_string, source_name)

  def _ParseStorageFileOptions(self, options):
    """Parses the storage file options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._storage_file_path = self.ParseStringOption(options, u'storage_file')
    if not self._storage_file_path:
      self._storage_file_path = self._GenerateStorageFileName()

  def AddStorageFileOptions(self, argument_group):
    """Adds the storage file options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup or argparse.ArgumentParser):
          argument group or argument parser.
    """
    argument_group.add_argument(
        u'--storage_file', action=u'store', metavar=u'STORAGE_FILE', nargs=u'?',
        type=str, default=None, help=u'The path of the storage file.')

  def ParseOptions(self, options):
    """Parses tool specific options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    super(ExtractionAndAnalysisTool, self).ParseOptions(options)
    self._ParseStorageFileOptions(options)
