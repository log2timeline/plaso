# -*- coding: utf-8 -*-
"""The storage media CLI tool."""

import os
import sys

from plaso.cli import tools
from plaso.frontend import storage_media_frontend
from plaso.lib import errors


class StorageMediaTool(tools.CLITool):
  """Class that implements a storage media CLI tool."""

  _DEFAULT_BYTES_PER_SECTOR = 512
  _SOURCE_OPTION = u'source'

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
    super(StorageMediaTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._partition_number = None
    self._partition_offset = None
    self._process_vss = False
    self._source_path = None
    self._vss_stores = None

  def _ParseStorageMediaImageOptions(self, options):
    """Parses the storage media image options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._partition_number = getattr(options, u'partition_number', None)
    if (self._partition_number is not None and
        isinstance(self._partition_number, basestring)):
      try:
        self._partition_number = int(self._partition_number, 10)
      except ValueError:
        raise errors.BadConfigOption(
            u'Invalid partition number: {0:s}.'.format(self._partition_number))

    self._partition_offset = getattr(options, u'image_offset_bytes', None)
    if (self._partition_offset is not None and
        isinstance(self._partition_offset, basestring)):
      try:
        self._partition_offset = int(self._partition_offset, 10)
      except ValueError:
        raise errors.BadConfigOption(
            u'Invalid image offset bytes: {0:s}.'.format(
                self._partition_offset))

    if self._partition_offset is None and hasattr(options, u'image_offset'):
      image_offset = getattr(options, u'image_offset')
      bytes_per_sector = getattr(
          options, u'bytes_per_sector', self._DEFAULT_BYTES_PER_SECTOR)

      if isinstance(image_offset, basestring):
        try:
          image_offset = int(image_offset, 10)
        except ValueError:
          raise errors.BadConfigOption(
              u'Invalid image offset: {0:s}.'.format(image_offset))

      if isinstance(bytes_per_sector, basestring):
        try:
          bytes_per_sector = int(bytes_per_sector, 10)
        except ValueError:
          raise errors.BadConfigOption(
              u'Invalid bytes per sector: {0:s}.'.format(bytes_per_sector))

      if image_offset:
        self._partition_offset = image_offset * bytes_per_sector

  def _ParseVssProcessingOptions(self, options):
    """Parses the VSS processing options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._process_vss = not getattr(options, u'no_vss', False)
    if self._process_vss:
      vss_stores = getattr(options, u'vss_stores', None)
    else:
      vss_stores = None

    if vss_stores:
      vss_stores = storage_media_frontend.StorageMediaFrontend.ParseVssStores(
          vss_stores)

    self._vss_stores = vss_stores

  def AddStorageMediaImageOptions(self, argument_group):
    """Adds the storage media image options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        u'--partition', dest=u'partition_number', action=u'store', type=int,
        default=None, help=(
            u'Choose a partition number from a disk image. This partition '
            u'number should correspond to the partion number on the disk '
            u'image, starting from partition 1.'))

    argument_group.add_argument(
        u'-o', u'--offset', dest=u'image_offset', action=u'store', default=None,
        type=int, help=(
            u'The offset of the volume within the storage media image in '
            u'number of sectors. A sector is {0:d} bytes in size by default '
            u'this can be overwritten with the --sector_size option.').format(
                self._DEFAULT_BYTES_PER_SECTOR))

    argument_group.add_argument(
        u'--sector_size', u'--sector-size', dest=u'bytes_per_sector',
        action=u'store', type=int, default=self._DEFAULT_BYTES_PER_SECTOR,
        help=(
            u'The number of bytes per sector, which is {0:d} by '
            u'default.').format(self._DEFAULT_BYTES_PER_SECTOR))

    argument_group.add_argument(
        u'--ob', u'--offset_bytes', u'--offset_bytes',
        dest=u'image_offset_bytes', action=u'store', default=None, type=int,
        help=(
            u'The offset of the volume within the storage media image in '
            u'number of bytes.'))

  def AddVssProcessingOptions(self, argument_group):
    """Adds the VSS processing options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        u'--no_vss', u'--no-vss', dest=u'no_vss', action=u'store_true',
        default=False, help=(
            u'Do not scan for Volume Shadow Snapshots (VSS). This means that '
            u'VSS information will not be included in the extraction phase.'))

    argument_group.add_argument(
        u'--vss_stores', u'--vss-stores', dest=u'vss_stores', action=u'store',
        type=str, default=None, help=(
            u'Define Volume Shadow Snapshots (VSS) (or stores that need to be '
            u'processed. A range of stores can be defined as: "3..5". '
            u'Multiple stores can be defined as: "1,3,5" (a list of comma '
            u'separated values). Ranges and lists can also be combined as: '
            u'"1,3..5". The first store is 1. All stores can be defined as: '
            u'"all".'))

  def ParseOptions(self, options):
    """Parses tool specific options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    super(StorageMediaTool, self).ParseOptions(options)
    self._ParseStorageMediaImageOptions(options)
    self._ParseVssProcessingOptions(options)

    self._source_path = getattr(options, self._SOURCE_OPTION, None)
    if not self._source_path:
      raise errors.BadConfigOption(u'Missing source path.')

    if isinstance(self._source_path, str):
      encoding = sys.stdin.encoding

      # Note that sys.stdin.encoding can be None.
      if not encoding:
        encoding = self.preferred_encoding

      # Note that the source path option can be an encoded byte string
      # and we need to turn it into an Unicode string.
      try:
        self._source_path = unicode(
            self._source_path.decode(encoding))
      except UnicodeDecodeError as exception:
        raise errors.BadConfigOption((
            u'Unable to convert source path to Unicode with error: '
            u'{0:s}.').format(exception))

    elif not isinstance(self._source_path, unicode):
      raise errors.BadConfigOption(
          u'Unsupported source path, string type required.')

    self._source_path = os.path.abspath(self._source_path)
