# -*- coding: utf-8 -*-
"""The extraction and analysis CLI tool."""

import datetime
import os

from plaso.cli import status_view_tool
from plaso.lib import errors


class ExtractionAndAnalysisTool(status_view_tool.StatusViewTool):
  """Class that implements an extraction and analysis CLI tool."""

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader (InputReader): the input reader.
                    The default is None which indicates the use of the stdin
                    input reader.
      output_writer (OutputWriter): the output writer.
                     The default is None which indicates the use of the stdout
                     output writer.
    """
    super(ExtractionAndAnalysisTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._storage_file_path = None

  def SetSourcePath(self, path):
    """Set the path of the source to process.

    Args:
      path (str): the path to the source.
    """
    self._source_path = path

  def _GenerateStorageFileName(self):
    """Generates a name for the storage file.

    This uses the MD5 hex digest of the source path plus a timestamp.

    Raises:
      BadConfigOption: raised if the source path is not set.
    """
    if not self._source_path:
      raise errors.BadConfigOption(u'Please define a source (--source).')

    timestamp = datetime.datetime.now()
    timestamp_text = timestamp.strftime(u'%Y%m%dT%H%M%S')
    source_name = os.path.basename(self._source_path)
    filename = u'{0:s}-{1:s}.plaso'.format(timestamp_text, source_name)
    return filename

  def _ParseStorageFileOptions(self, options):
    """Parses the storage file options.

    Args:
      options (argparse.Namespace): the command line arguments.

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
                     the argument group our argument parser.
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
