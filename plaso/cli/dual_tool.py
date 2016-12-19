# -*- coding: utf-8 -*-
"""The dual CLI tool."""

import datetime
import md5

from plaso.cli import status_view_tool
from plaso.lib import errors

class DualTool(status_view_tool.StatusViewTool):
  """Class that implements an extraction and analysis CLI tool."""

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
    super(DualTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._storage_file_path = None

  def SetSourcePath(self, path):
    """Set the path of the source to process.

    Args:
      path: a string for the path to the source.
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

    md5_factory = md5.new()
    md5_factory.update(self._source_path.encode('utf-8'))
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = "{0:s}-{1:s}.plaso".format(timestamp, md5_factory.hexdigest())
    return filename

  def _ParseStorageFileOptions(self, options):
    """Parses the storage file options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._storage_file_path = self.ParseStringOption(options, u'storage_file')
    if not self._storage_file_path:
      self._storage_file_path = self._GenerateStorageFileName()

  def AddStorageFileOptions(self, argument_group):
    """Adds the storage file options to the argument group.

    Args:
      argument_group: the argparse argument group (instance of
                      argparse._ArgumentGroup) or argument parser (instance of
                      argparse.ArgumentParser).
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
    super(DualTool, self).ParseOptions(options)
    self._ParseStorageFileOptions(options)
