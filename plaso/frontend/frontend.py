#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The common front-end functionality."""

from plaso.collector import scanner


class Frontend(object):
  """Class that implements a front-end."""

  def __init__(self):
    """Initializes the front-end object."""
    super(Frontend, self).__init__()
    self._input_reader = scanner.StdinScannerInputReader()
    self._output_writer = scanner.StdoutScannerOutputWriter()

  def AddImageOptions(self, argument_group):
    """Adds the storage media image options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        '-o', '--offset', dest='image_offset', action='store', default=None,
        type=int, help=(
            u'The offset of the volume within the storage media image in '
            u'number of sectors. A sector is 512 bytes in size by default '
            u'this can be overwritten with the --sector_size option.'))

    argument_group.add_argument(
        '--sector_size', '--sector-size', dest='bytes_per_sector',
        action='store', type=int, default=512, help=(
            u'The number of bytes per sector, which is 512 by default.'))

    argument_group.add_argument(
        '--ob', '--offset_bytes', '--offset_bytes', dest='image_offset_bytes',
        action='store', default=None, type=int, help=(
            u'The offset of the volume within the storage media image in '
            u'number of bytes.'))

  def AddVssProcessingOptions(self, argument_group):
    """Adds the VSS processing options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        '--vss_stores', '--vss-stores', dest='vss_stores', action='store',
        type=str, default=None, help=(
            u'Define Volume Shadow Snapshots (VSS) (or stores that need to be '
            u'processed. A range of stores can be defined as: \'3..5\'. '
            u'Multiple stores can be defined as: \'1,3,5\' (a list of comma '
            u'separated values). Ranges and lists can also be combined as: '
            u'\'1,3..5\'. The first store is 1.'))

  def PrintOptions(self, options):
    """Prints the options.

    Args:
      options: the command line arguments.
    """
    self._output_writer.Write(u'\n')
    self._output_writer.Write(
        u'Source\t\t\t: {0:s}\n'.format(options.source))
    self._output_writer.Write(
        u'Is storage media image\t: {0!s}\n'.format(options.image))

    if options.image:
      self._output_writer.Write(
          u'Partition offset\t: 0x{0:08x}\n'.format(options.image_offset_bytes))

      if options.vss_stores:
        self._output_writer.Write(
            u'VSS stores\t\t: {0!s}\n'.format(options.vss_stores))

    if options.file_filter:
      self._output_writer.Write(
          u'Filter file\t\t: {0:s}\n'.format(options.file_filter))

    self._output_writer.Write(u'\n')

  def ScanSource(self, options, source_option):
    """Scans the source for volume and file systems.

    Args:
      options: the command line arguments.
      source_option: the name of the source option.

    Returns:
      The base path specification (instance of dfvfs.PathSpec).
    """
    source = getattr(options, source_option, None)
    if not source:
      return

    file_system_scanner = scanner.FileSystemScanner(
        input_reader=self._input_reader, output_writer=self._output_writer)

    if hasattr(options, 'image_offset_bytes'):
      file_system_scanner.SetPartitionOffset(options.image_offset_bytes)
    elif hasattr(options, 'image_offset'):
      bytes_per_sector = getattr(options, 'bytes_per_sector', 512)
      file_system_scanner.SetPartitionOffset(
          options.image_offset * bytes_per_sector)

    if getattr(options, 'partition_number', None) is not None:
      file_system_scanner.SetPartitionNumber(options.partition_number)

    if hasattr(options, 'vss_stores'):
      file_system_scanner.SetVssStores(options.vss_stores)

    path_spec = file_system_scanner.Scan(source)

    options.image = file_system_scanner.is_storage_media_image
    options.image_offset_bytes = file_system_scanner.partition_offset
    options.vss_stores = file_system_scanner.vss_stores

    return path_spec
