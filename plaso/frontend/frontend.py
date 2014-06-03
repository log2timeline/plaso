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

import abc
import locale
import logging
import multiprocessing
import os
import pdb
import signal
import sys
import threading
import traceback

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import context
from dfvfs.volume import tsk_volume_system
from dfvfs.volume import vshadow_volume_system

import plaso
from plaso import parsers   # pylint: disable=unused-import
from plaso.engine import engine
from plaso.engine import scanner
from plaso.engine import utils as engine_utils
from plaso.frontend import rpc_proxy
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import foreman
from plaso.lib import pfilter
from plaso.lib import putils
from plaso.lib import queue
from plaso.lib import storage
from plaso.lib import timelib

import pytz


class FrontendInputReader(object):
  """Class that implements the input reader interface for the engine."""

  @abc.abstractmethod
  def Read(self):
    """Reads a string from the input.

    Returns:
      A string containing the input.
    """


class FrontendOutputWriter(object):
  """Class that implements the output writer interface for the engine."""

  @abc.abstractmethod
  def Write(self, string):
    """Wtites a string to the output.

    Args:
      string: A string containing the output.
    """


class StdinFrontendInputReader(object):
  """Class that implements a stdin input reader."""

  def Read(self):
    """Reads a string from the input.

    Returns:
      A string containing the input.
    """
    return sys.stdin.readline()


class StdoutFrontendOutputWriter(object):
  """Class that implements a stdout output writer."""

  ENCODING = u'utf-8'

  def Write(self, string):
    """Writes a string to the output.

    Args:
      string: A string containing the output.
    """
    try:
      sys.stdout.write(string.encode(self.ENCODING))
    except UnicodeEncodeError:
      logging.error(
          u'Unable to properly write output, line will be partially '
          u'written out.')
      sys.stdout.write(u'LINE ERROR')
      sys.stdout.write(string.encode(self.ENCODING, 'ignore'))


class Frontend(object):
  """Class that implements a front-end."""

  # The maximum length of the line in number of charcters.
  _LINE_LENGTH = 80

  def __init__(self, input_reader, output_writer):
    """Initializes the front-end object.

    Args:
      input_reader: the input reader (instance of FrontendInputReader).
                    The default is None which indicates to use the stdin
                    input reader.
      output_writer: the output writer (instance of FrontendOutputWriter).
                     The default is None which indicates to use the stdout
                     output writer.
    """
    super(Frontend, self).__init__()
    self._input_reader = input_reader
    self._output_writer = output_writer

    # TODO: add preferred_encoding support ot output writer.
    self.preferred_encoding = locale.getpreferredencoding().lower()

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

  def PrintColumnValue(self, name, description, column_length=25):
    """Prints a value with a name and description aligned to the column length.

    Args:
      name: The name.
      description: The description.
      column_length: Optional column length. The default is 25.
    """
    line_length = self._LINE_LENGTH - column_length - 3

    # The format string of the first line of the column value.
    primary_format_string = u'{{0:>{0:d}s}} : {{1:s}}\n'.format(column_length)

    # The format string of successive lines of the column value.
    secondary_format_string = u'{{0:<{0:d}s}}{{1:s}}\n'.format(
        column_length + 3)

    if len(description) < line_length:
      self._output_writer.Write(primary_format_string.format(name, description))
      return

    # Split the description in words.
    words = description.split()

    current = 0

    lines = []
    word_buffer = []
    for word in words:
      current += len(word) + 1
      if current >= line_length:
        current = len(word)
        lines.append(u' '.join(word_buffer))
        word_buffer = [word]
      else:
        word_buffer.append(word)
    lines.append(u' '.join(word_buffer))

    # Print the column value on multiple lines.
    self._output_writer.Write(primary_format_string.format(name, lines[0]))
    for line in lines[1:]:
      self._output_writer.Write(secondary_format_string.format(u'', line))

  def PrintHeader(self, text, character='*'):
    """Prints the header as a line with centered text.

    Args:
      text: The header text.
      character: Optional header line character. The default is '*'.
    """
    self._output_writer.Write(u'\n')

    format_string = u'{{0:{0:s}^{1:d}}}\n'.format(character, self._LINE_LENGTH)
    header_string = format_string.format(u' {0:s} '.format(text))
    self._output_writer.Write(header_string)

  def PrintOptions(self, options, source_path):
    """Prints the options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      source_path: the source path.
    """
    self._output_writer.Write(u'\n')
    self._output_writer.Write(
        u'Source path\t\t: {0:s}\n'.format(source_path))

    if self._source_type == self._SOURCE_TYPE_STORAGE_MEDIA_IMAGE:
      is_image = True
    else:
      is_image = False

    self._output_writer.Write(
        u'Is storage media image\t: {0!s}\n'.format(is_image))

    if is_image:
      image_offset_bytes = self._partition_offset
      if isinstance(image_offset_bytes, basestring):
        try:
          image_offset_bytes = int(image_offset_bytes, 10)
        except ValueError:
          image_offset_bytes = 0
      elif image_offset_bytes is None:
        image_offset_bytes = 0

      self._output_writer.Write(
          u'Partition offset\t: {0:d} (0x{0:08x})\n'.format(image_offset_bytes))

      vss_stores = getattr(options, 'vss_stores', None)
      if vss_stores:
        self._output_writer.Write(u'VSS stores\t\t: {0!s}\n'.format(vss_stores))

    filter_file = getattr(options, 'file_filter', None)
    if filter_file:
      self._output_writer.Write(u'Filter file\t\t: {0:s}\n'.format(filter_file))

    self._output_writer.Write(u'\n')

  def PrintSeparatorLine(self):
    """Prints a separator line."""
    self._output_writer.Write(u'{0:s}\n'.format(u'-' * self._LINE_LENGTH))


class ExtractionFrontend(Frontend):
  """Class that implements an extraction front-end."""

  # The minimum number of processes.
  MINIMUM_WORKERS = 2
  # The maximum number of processes.
  MAXIMUM_WORKERS = 15

  _SOURCE_TYPE_DEVICE = 1
  _SOURCE_TYPE_DIRECTORY = 2
  _SOURCE_TYPE_FILE = 3
  _SOURCE_TYPE_STORAGE_MEDIA_IMAGE = 4

  def __init__(self, input_reader, output_writer):
    """Initializes the front-end object.

    Args:
      input_reader: the input reader (instance of FrontendInputReader).
                    The default is None which indicates to use the stdin
                    input reader.
      output_writer: the output writer (instance of FrontendOutputWriter).
                     The default is None which indicates to use the stdout
                     output writer.
    """
    super(ExtractionFrontend, self).__init__(input_reader, output_writer)
    self._collection_process = None
    self._collector = None
    self._debug_mode = False
    self._engine = None
    self._file_system_scanner = scanner.FileSystemScanner()
    self._filter_expression = None
    self._filter_object = None
    self._number_of_worker_processes = 0
    self._parsers = None
    self._partition_offset = None
    self._preprocess = False
    self._resolver_context = context.Context()
    self._run_foreman = True
    self._single_process_mode = False
    self._show_worker_memory_information = False
    self._source_path = None
    self._source_path_spec = None
    self._source_type = None
    self._storage_file_path = None
    self._storage_process = None
    self._timezone = pytz.utc
    self._vss_stores = None

    # TODO: turn into a process pool.
    self._worker_processes = {}

  def _CheckStorageFile(self, storage_file_path):
    """Checks if the storage file path is valid.

    Args:
      storage_file_path: The path of the storage file.

    Raises:
      BadConfigOption: if the storage file path is invalid.
    """
    if os.path.exists(storage_file_path):
      if not os.path.isfile(storage_file_path):
        raise errors.BadConfigOption(
            u'Storage file: {0:s} already exists and is not a file.'.format(
                storage_file_path))
      logging.warning(u'Appending to an already existing storage file.')

    dirname = os.path.dirname(storage_file_path)
    if not dirname:
      dirname = '.'

    # TODO: add a more thorough check to see if the storage file really is
    # a plaso storage file.

    if not os.access(dirname, os.W_OK):
      raise errors.BadConfigOption(
          u'Unable to write to storage file: {0:s}'.format(storage_file_path))

  def _CreateExtractionWorker(self, worker_number, options, pre_obj):
    """Creates an extraction worker object.

    Args:
      worker_number: number that identifies the worker.
      options: the command line arguments (instance of argparse.Namespace).
      pre_obj: The preprocessing object (instance of PreprocessObject).

    Returns:
      An extraction worker (instance of worker.ExtractionWorker).
    """
    # Set up a simple XML RPC server for the worker for status indications.
    # Since we don't know the worker's PID for now we'll set the initial port
    # number to zero and then adjust it later.
    proxy_server = rpc_proxy.StandardRpcProxyServer()
    extraction_worker = self._engine.CreateExtractionWorker(
        worker_number, pre_obj, self._parsers, rpc_proxy=proxy_server)

    extraction_worker.SetDebugMode(self._debug_mode)
    extraction_worker.SetSingleProcessMode(self._single_process_mode)

    open_files = getattr(options, 'open_files', None)
    extraction_worker.SetOpenFiles(open_files)

    if getattr(options, 'os', None):
      mount_path = getattr(options, 'filename', None)
      extraction_worker.SetMountPath(mount_path)

    filter_query = getattr(options, 'filter', None)
    if filter_query:
      filter_object = pfilter.GetMatcher(filter_query)
      extraction_worker.SetFilterObject(filter_object)

    text_prepend = getattr(options, 'text_prepend', None)
    extraction_worker.SetTextPrepend(text_prepend)

    return extraction_worker

  def _DebugPrintCollector(self, options):
    """Prints debug information about the collector.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    filter_file = getattr(options, 'file_filter', None)
    if self._source_type == self._SOURCE_TYPE_STORAGE_MEDIA_IMAGE:
      if filter_file:
        logging.debug(u'Starting a collection on image with filter.')
      else:
        logging.debug(u'Starting a collection on image.')

    elif self._source_type == self._SOURCE_TYPE_DIRECTORY:
      if filter_file:
        logging.debug(u'Starting a collection on directory with filter.')
      else:
        logging.debug(u'Starting a collection on directory.')

    elif self._source_type == self._SOURCE_TYPE_FILE:
      logging.debug(u'Starting a collection on a single file.')

    else:
      logging.warning(u'Unsupported source type.')

  def _GetPartionIdentifierFromUser(self, volume_system, volume_identifiers):
    """Asks the user to provide the partitioned volume identifier.

    Args:
      volume_system: The volume system (instance of dfvfs.TSKVolumeSystem).
      volume_identifiers: List of allowed volume identifiers.

    Raises:
      FileSystemScannerError: if the source cannot be processed.
    """
    self._output_writer.Write(
        u'The following partitions were found:\n'
        u'Identifier\tOffset (in bytes)\tSize (in bytes)\n')

    for volume_identifier in volume_identifiers:
      volume = volume_system.GetVolumeByIdentifier(volume_identifier)
      if not volume:
        raise errors.FileSystemScannerError(
            u'Volume missing for identifier: {0:s}.'.format(volume_identifier))

      volume_extent = volume.extents[0]
      self._output_writer.Write(
          u'{0:s}\t\t{1:d} (0x{1:08x})\t{2:d}\n'.format(
              volume.identifier, volume_extent.offset, volume_extent.size))

    self._output_writer.Write(u'\n')

    while True:
      self._output_writer.Write(
          u'Please specify the identifier of the partition that should '
          u'be processed:\nNote that you can abort with Ctrl^C.\n')

      selected_volume_identifier = self._input_reader.Read()
      selected_volume_identifier = selected_volume_identifier.strip()

      if selected_volume_identifier in volume_identifiers:
        break

      self._output_writer.Write(
          u'\n'
          u'Unsupported partition identifier, please try again or abort '
          u'with Ctrl^C.\n'
          u'\n')

    return selected_volume_identifier

  def _GetVolumeTSKPartition(
      self, volume_system_path_spec, partition_number=None,
      partition_offset=None):
    """Determines the volume path specification.

    Args:
      volume_system_path_spec: the volume system path specification (instance
                               of dfvfs.PathSpec).
      partition_number: Optional preferred partition number. The default is
                        None.
      partition_offset: Optional preferred partition byte offset. The default
                        is None.

    Returns:
      The TSK partition volume path specification (instance of dfvfs.PathSpec)
      or None if no supported partition was found.

    Raises:
      FileSystemScannerError: if the format of or within the source
                              is not supported.
      RuntimeError: if the volume for a specific identifier cannot be
                    retrieved.
    """
    volume_system = tsk_volume_system.TSKVolumeSystem()
    volume_system.Open(volume_system_path_spec)

    volume_identifiers = self._file_system_scanner.GetVolumeIdentifiers(
        volume_system)

    if not volume_identifiers:
      logging.info(u'No supported partitions found.')
      return

    if partition_number is not None and partition_number > 0:
      # Plaso uses partition numbers starting with 1 while dfvfs expects
      # the volume index to start with 0.
      partition_number -= 1

      volume = volume_system.GetVolumeByIndex(partition_number)

      if volume:
        volume_extent = volume.extents[0]
        self._partition_offset = volume_extent.offset
        return path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION,
            start_offset=volume_extent.offset,
            parent=volume_system_path_spec.parent)

      logging.warning(u'No such partition: {0:d}.'.format(partition_number))

    if partition_offset is not None:
      for volume in volume_system.volumes:
        volume_extent = volume.extents[0]
        if volume_extent.offset == partition_offset:
          self._partition_offset = volume_extent.offset
          return path_spec_factory.Factory.NewPathSpec(
              dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION,
              start_offset=volume_extent.offset,
              parent=volume_system_path_spec.parent)

      logging.warning(
          u'No such partition with offset: {0:d} (0x{0:08x}).'.format(
              partition_offset))

    if len(volume_identifiers) == 1:
      volume = volume_system.GetVolumeByIdentifier(volume_identifiers[0])
      if not volume:
        raise RuntimeError(
            u'Unable to retieve volume by identifier: {0:s}'.format(
                volume_identifiers[0]))

      volume_extent = volume.extents[0]
      self._partition_offset = volume_extent.offset
      return path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION, location=u'/p1',
          parent=volume_system_path_spec.parent)

    try:
      selected_volume_identifier = self._GetPartionIdentifierFromUser(
          volume_system, volume_identifiers)
    except KeyboardInterrupt:
      raise errors.FileSystemScannerError(u'File system scan aborted.')

    location = u'/{0:s}'.format(selected_volume_identifier)

    volume = volume_system.GetVolumeByIdentifier(selected_volume_identifier)
    if not volume:
      raise RuntimeError(
          u'Unable to retieve volume by identifier: {0:s}'.format(
              selected_volume_identifier))

    volume_extent = volume.extents[0]
    self._partition_offset = volume_extent.offset
    return path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION, location=location,
        parent=volume_system_path_spec.parent)

  def _GetVolumeVssStoreIdentifiers(
      self, volume_system_path_spec, vss_stores=None):
    """Determines the VSS store identifiers.

    Args:
      volume_system_path_spec: the volume system path specification (instance
                               of dfvfs.PathSpec).
      vss_stores: Optional list of preferred VSS stored identifiers. The
                  default is None.

    Returns:
      None to indicate no sub volume system was found.

    Raises:
      FileSystemScannerError: if the format of or within the source
                              is not supported.
    """
    volume_system = vshadow_volume_system.VShadowVolumeSystem()
    volume_system.Open(volume_system_path_spec)

    volume_identifiers = self._file_system_scanner.GetVolumeIdentifiers(
        volume_system)

    if not volume_identifiers:
      return

    try:
      self._vss_stores = self._GetVssStoreIdentifiersFromUser(
          volume_system, volume_identifiers, vss_stores=vss_stores)
    except KeyboardInterrupt:
      raise errors.FileSystemScannerError(u'File system scan aborted.')

    return

  def _GetVssStoreIdentifiersFromUser(
      self, volume_system, volume_identifiers, vss_stores=None):
    """Asks the user to provide the VSS store identifiers.

    Args:
      volume_system: The volume system (instance of dfvfs.VShadowVolumeSystem).
      volume_identifiers: List of allowed volume identifiers.
      vss_stores: Optional list of preferred VSS stored identifiers. The
                  default is None.

    Returns:
      The list of selected VSS store identifiers or None.

    Raises:
      FileSystemScannerError: if the source cannot be processed.
    """
    normalized_volume_identifiers = []
    for volume_identifier in volume_identifiers:
      volume = volume_system.GetVolumeByIdentifier(volume_identifier)
      if not volume:
        raise errors.FileSystemScannerError(
            u'Volume missing for identifier: {0:s}.'.format(volume_identifier))

      try:
        volume_identifier = int(volume.identifier[3:], 10)
        normalized_volume_identifiers.append(volume_identifier)
      except ValueError:
        pass

    if vss_stores:
      if not set(vss_stores).difference(
          normalized_volume_identifiers):
        return vss_stores

    print_header = True
    while True:
      if print_header:
        self._output_writer.Write(
            u'The following Volume Shadow Snapshots (VSS) were found:\n'
            u'Identifier\tVSS store identifier\tCreation Time\n')

        for volume_identifier in volume_identifiers:
          volume = volume_system.GetVolumeByIdentifier(volume_identifier)
          if not volume:
            raise errors.FileSystemScannerError(
                u'Volume missing for identifier: {0:s}.'.format(
                    volume_identifier))

          vss_identifier = volume.GetAttribute('identifier')
          vss_creation_time = volume.GetAttribute('creation_time')
          vss_creation_time = timelib.Timestamp.FromFiletime(
              vss_creation_time.value)
          vss_creation_time = timelib.Timestamp.CopyToIsoFormat(
              vss_creation_time)
          self._output_writer.Write(u'{0:s}\t\t{1:s}\t{2:s}\n'.format(
              volume.identifier, vss_identifier.value, vss_creation_time))

        self._output_writer.Write(u'\n')

        print_header = False

      self._output_writer.Write(
          u'Please specify the identifier(s) of the VSS that should be '
          u'processed:\nNote that a range of stores can be defined as: 3..5. '
          u'Multiple stores can\nbe defined as: 1,3,5 (a list of comma '
          u'separated values). Ranges and lists can\nalso be combined '
          u'as: 1,3..5. The first store is 1. If no stores are specified\n'
          u'none will be processed. You can abort with Ctrl^C.\n')

      selected_vss_stores = self._input_reader.Read()

      selected_vss_stores = selected_vss_stores.strip()
      if not selected_vss_stores:
        break

      try:
        selected_vss_stores = self._file_system_scanner.ParseVssStores(
            selected_vss_stores)
      except errors.BadConfigOption:
        selected_vss_stores = []

      if not set(selected_vss_stores).difference(normalized_volume_identifiers):
        break

      self._output_writer.Write(
          u'\n'
          u'Unsupported VSS identifier(s), please try again or abort with '
          u'Ctrl^C.\n'
          u'\n')

    return selected_vss_stores

  # TODO: have the frontend fill collecton information gradually
  # and set it as the last step of preprocessing?
  def _PreprocessSetCollectionInformation(self, options, pre_obj):
    """Sets the collection information as part of the preprocessing.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      pre_obj: the preprocess object (instance of PreprocessObject).
    """
    collection_information = {}

    collection_information['version'] = plaso.GetVersion()
    collection_information['configured_zone'] = self._timezone
    collection_information['file_processed'] = self._source_path
    collection_information['output_file'] = self._storage_file_path
    collection_information['protobuf_size'] = self._buffer_size
    collection_information['parser_selection'] = getattr(
        options, 'parsers', '(no list set)')
    collection_information['preferred_encoding'] = self.preferred_encoding
    collection_information['time_of_run'] = timelib.Timestamp.GetNow()

    collection_information['parsers'] = self._parser_names
    collection_information['preprocess'] = self._preprocess

    if self._source_type == self._SOURCE_TYPE_DIRECTORY:
      recursive = True
    else:
      recursive = False
    collection_information['recursive'] = recursive
    collection_information['debug'] = self._debug_mode
    collection_information['vss parsing'] = bool(self._vss_stores)

    if self._filter_expression:
      collection_information['filter'] = self._filter_expression

    filter_file = getattr(options, 'file_filter', None)
    if filter_file:
      if os.path.isfile(filter_file):
        filters = []
        with open(filter_file, 'rb') as fh:
          for line in fh:
            filters.append(line.rstrip())
        collection_information['file_filter'] = ', '.join(filters)

    collection_information['os_detected'] = getattr(options, 'os', 'N/A')

    if self._source_type == self._SOURCE_TYPE_STORAGE_MEDIA_IMAGE:
      collection_information['method'] = 'imaged processed'
      collection_information['image_offset'] = self._partition_offset
    else:
      collection_information['method'] = 'OS collection'

    if self._single_process_mode:
      collection_information['runtime'] = 'single process mode'
    else:
      collection_information['runtime'] = 'multi process mode'
      collection_information['workers'] = self._number_of_worker_processes

    pre_obj.collection_information = collection_information

  def _PreprocessSetParserFilter(self, options, pre_obj):
    """Sets the parser filter as part of the preprocessing.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      pre_obj: The previously created preprocessing object (instance of
               PreprocessObject) or None.
    """
    # TODO: Make this more sane. Currently we are only checking against
    # one possible version of Windows, and then making the assumption if
    # that is not correct we default to Windows 7. Same thing with other
    # OS's, no assumption or checks are really made there.
    # Also this is done by default, and no way for the user to turn off
    # this behavior, need to add a parameter to the frontend that takes
    # care of overwriting this behavior.

    # TODO: refactor putting the filter into the options object.
    # See if it can be passed in another way.
    if not getattr(options, 'filter', None):
      options.filter = u''

    if not options.filter:
      options.filter = u''

    parser_filter_string = u''

    # If no parser filter is set, let's use our best guess of the OS
    # to build that list.
    if not getattr(options, 'parsers', ''):
      if hasattr(pre_obj, 'osversion'):
        os_version = pre_obj.osversion.lower()
        # TODO: Improve this detection, this should be more 'intelligent', since
        # there are quite a lot of versions out there that would benefit from
        # loading up the set of 'winxp' parsers.
        if 'windows xp' in os_version:
          parser_filter_string = 'winxp'
        elif 'windows server 2000' in os_version:
          parser_filter_string = 'winxp'
        elif 'windows server 2003' in os_version:
          parser_filter_string = 'winxp'
        else:
          parser_filter_string = 'win7'

      if getattr(pre_obj, 'guessed_os', None):
        if pre_obj.guessed_os == 'MacOSX':
          parser_filter_string = u'macosx'
        elif pre_obj.guessed_os == 'Linux':
          parser_filter_string = 'linux'

      if parser_filter_string:
        options.parsers = parser_filter_string
        logging.info(u'Parser filter expression changed to: {0:s}'.format(
            options.parsers))

  def _PreprocessSetTimezone(self, options, pre_obj):
    """Sets the timezone as part of the preprocessing.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      pre_obj: The previously created preprocessing object (instance of
               PreprocessObject) or None.
    """
    if hasattr(pre_obj, 'time_zone_str'):
      logging.info(u'Setting timezone to: {0:s}'.format(pre_obj.time_zone_str))
      try:
        pre_obj.zone = pytz.timezone(pre_obj.time_zone_str)
      except pytz.UnknownTimeZoneError:
        if hasattr(options, 'zone'):
          logging.warning((
              u'Unable to automatically configure timezone, falling back '
              u'to the user supplied one: {0:s}').format(self._timezone))
          pre_obj.zone = self._timezone
        else:
          logging.warning(u'TimeZone was not properly set, defaulting to UTC')
          pre_obj.zone = pytz.utc
    else:
      # TODO: shouldn't the user to be able to always override the timezone
      # detection? Or do we need an input sanitation function.
      pre_obj.zone = self._timezone

    if not getattr(pre_obj, 'zone', None):
      pre_obj.zone = self._timezone

  def _ProcessSourceMultiProcessMode(self, options):
    """Processes the source in a multiple process.

    Muliprocessing is used to start up separate processes.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    # TODO: replace by an option.
    start_collection_process = True

    self._number_of_worker_processes = getattr(options, 'workers', 0)
    if self._number_of_worker_processes < 1:
      # One worker for each "available" CPU (minus other processes).
      # The number three here is derived from the fact that the engine starts
      # up:
      #   + A collector process.
      #   + A storage process.
      # If we want to utilize all CPU's on the system we therefore need to start
      # up workers that amounts to the total number of CPU's - 3 (these two plus
      # the main process). Thus the number three.
      cpus = multiprocessing.cpu_count() - 3

      if cpus <= self.MINIMUM_WORKERS:
        cpus = self.MINIMUM_WORKERS
      elif cpus >= self.MAXIMUM_WORKERS:
        # Let's have a maximum amount of workers.
        cpus = self.MAXIMUM_WORKERS

      self._number_of_worker_processes = cpus

    logging.info(u'Starting extraction in multi process mode.')

    collection_queue = queue.MultiThreadedQueue()
    storage_queue = queue.MultiThreadedQueue()
    self._engine = engine.Engine(collection_queue, storage_queue)

    self._engine.SetSource(
        self._source_path_spec, resolver_context=self._resolver_context)

    logging.debug(u'Starting preprocessing.')
    pre_obj = self.PreprocessSource(options)

    # TODO: move FindAllParsers to engine as a class method?
    filter_query = getattr(options, 'parsers', '')
    self._parsers = putils.FindAllParsers(
        pre_obj=pre_obj, config=options, parser_filter_string=filter_query)
    self._parser_names = [parser.parser_name for parser in self._parsers['all']]

    self._PreprocessSetCollectionInformation(options, pre_obj)

    output_module = getattr(options, 'output_module', None)
    if output_module:
      storage_writer = storage.BypassStorageWriter(
          storage_queue, self._storage_file_path,
          output_module_string=output_module, pre_obj=pre_obj)
    else:
      storage_writer = storage.StorageFileWriter(
          storage_queue, self._storage_file_path, self._buffer_size, pre_obj)

    logging.debug(u'Preprocessing done.')

    if 'filestat' in self._parser_names:
      include_directory_stat = True
    else:
      include_directory_stat = False

    filter_file = getattr(options, 'file_filter', None)
    if filter_file:
      filter_find_specs = engine_utils.BuildFindSpecsFromFile(
          filter_file, pre_obj=pre_obj)
    else:
      filter_find_specs = None

    if start_collection_process:
      resolver_context = context.Context()
    else:
      resolver_context = self._resolver_context

    engine_proxy = None
    rpc_proxy_client = None

    if self._run_foreman:
      worker_foreman = foreman.Foreman(
          show_memory_usage=self._show_worker_memory_information)

      # Start a proxy server (only needed when a foreman is started).
      engine_proxy = rpc_proxy.StandardRpcProxyServer(os.getpid())
      try:
        engine_proxy.Open()
        engine_proxy.RegisterFunction(
            'signal_end_of_collection', worker_foreman.SignalEndOfProcessing)

        proxy_thread = threading.Thread(
            name='rpc_proxy', target=engine_proxy.StartProxy)
        proxy_thread.start()

        rpc_proxy_client = rpc_proxy.StandardRpcProxyClient(
            engine_proxy.listening_port)
      except errors.ProxyFailedToStart as exception:
        proxy_thread = None
        logging.error((
            u'Unable to setup a RPC server for the engine with error '
            u'{0:s}').format(exception))
    else:
      worker_foreman = None

    self._collector = self._engine.CreateCollector(
        include_directory_stat, vss_stores=self._vss_stores,
        filter_find_specs=filter_find_specs, resolver_context=resolver_context)

    if rpc_proxy_client:
      self._collector.SetProxy(rpc_proxy_client)

    self._DebugPrintCollector(options)

    logging.info(u'Starting storage process.')
    self._storage_process = multiprocessing.Process(
        name='StorageThread', target=storage_writer.WriteEventObjects)
    self._storage_process.start()

    if start_collection_process:
      logging.info(u'Starting collection process.')
      self._collection_process = multiprocessing.Process(
          name='Collection', target=self._collector.Collect)
      self._collection_process.start()

    logging.info(u'Starting worker processes to extract events.')

    for worker_nr in range(self._number_of_worker_processes):
      extraction_worker = self._CreateExtractionWorker(
          worker_nr, options, pre_obj)

      logging.debug(u'Starting worker: {0:d} process'.format(worker_nr))
      worker_name = u'Worker_{0:d}'.format(worker_nr)
      # TODO: Test to see if a process pool can be a better choice.
      self._worker_processes[worker_name] = multiprocessing.Process(
          name=worker_name, target=extraction_worker.Run)

      self._worker_processes[worker_name].start()
      pid = self._worker_processes[worker_name].pid
      if worker_foreman:
        worker_foreman.MonitorWorker(pid=pid, name=worker_name)

    logging.info(u'Collecting and processing files.')
    if self._collection_process:
      while self._collection_process.is_alive():
        self._collection_process.join(10)
        # Check the worker status regularly while collection is still ongoing.
        if worker_foreman:
          worker_foreman.CheckStatus()
          # TODO: We get a signal when collection is done, which might happen
          # before the collection thread joins. Look at the option of speeding
          # up the process of the collector stopping by potentially killing it.
    else:
      self._collector.Collect()

    logging.info(u'Collection is done, waiting for processing to complete.')
    if worker_foreman:
      worker_foreman.SignalEndOfProcessing()

    # Close the RPC server since the collection thread is done.
    if engine_proxy:
      # Close the proxy, free up resources so we can shut down the thread.
      engine_proxy.Close()

      if proxy_thread.isAlive():
        proxy_thread.join()

    # Run through the running workers, one by one.
    # This will go through a list of all active worker processes and check it's
    # status. If a worker has completed it will be removed from the list.
    # The process will not wait longer than five seconds for each worker to
    # complete, if longer time passes it will simply check it's status and
    # move on. That ensures that worker process is monitored and status is
    # updated.
    while self._worker_processes:
      for process_name, process_obj in sorted(self._worker_processes.items()):
        if worker_foreman:
          worker_label = worker_foreman.GetLabel(
              name=process_name, pid=process_obj.pid)
        else:
          worker_label = None

        if not worker_label:
          if process_obj.is_alive():
            logging.info((
                u'Process {0:s} [{1:d}] is not monitored by the foreman. Most '
                u'likely due to a worker having completed it\'s processing '
                u'while waiting for another worker to complete.').format(
                    process_name, process_obj.pid))
            logging.info(
                u'Waiting for worker {0:s} to complete.'.format(process_name))
            process_obj.join()
            logging.info(u'Worker: {0:s} [{1:d}] has completed.'.format(
                process_name, process_obj.pid))

          del self._worker_processes[process_name]
          continue

        if process_obj.is_alive():
          # Check status of worker.
          worker_foreman.CheckStatus(label=worker_label)
          process_obj.join(5)
        # Note that we explicitly must test against exitcode 0 here since
        # process.exitcode will be None if there is no exitcode.
        elif process_obj.exitcode != 0:
          logging.warning((
              u'Worker process: {0:s} already exited with code: '
              u'{1:d}.').format(process_name, process_obj.exitcode))
          process_obj.terminate()
          worker_foreman.TerminateProcess(label=worker_label)

        else:
          # Process is no longer alive, no need to monitor.
          worker_foreman.StopMonitoringWorker(label=worker_label)
          # Remove it from our list of active workers.
          del self._worker_processes[process_name]

    logging.info(u'Processing is done, waiting for storage to complete.')

    self._engine.SignalEndOfInputStorageQueue()
    self._storage_process.join()
    logging.info(u'Storage is done.')

  def _ProcessSourceSingleProcessMode(self, options):
    """Processes the source in a single process.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    logging.info(u'Starting extraction in single process mode.')

    try:
      self._StartSingleThread(options)
    except Exception as exception:
      # The tool should generally not be run in single process mode
      # for other reasons than to debug. Hence the general error
      # catching.
      logging.error(u'An uncaught exception occured: {0:s}.\n{1:s}'.format(
          exception, traceback.format_exc()))
      if self._debug_mode:
        pdb.post_mortem()

  def _StartSingleThread(self, options):
    """Starts everything up in a single process.

    This should not normally be used, since running the tool in a single
    process buffers up everything into memory until the storage is called.

    Just to make it clear, this starts up the collection, completes that
    before calling the worker that extracts all EventObjects and stores
    them in memory. when that is all done, the storage function is called
    to drain the buffer. Hence the tool's excessive use of memory in this
    mode and the reason why it is not suggested to be used except for
    debugging reasons (and mostly to get into the debugger).

    This is therefore mostly useful during debugging sessions for some
    limited parsing.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    collection_queue = queue.SingleThreadedQueue()
    storage_queue = queue.SingleThreadedQueue()
    self._engine = engine.Engine(collection_queue, storage_queue)

    self._engine.SetSource(
        self._source_path_spec, resolver_context=self._resolver_context)

    logging.debug(u'Starting preprocessing.')
    pre_obj = self.PreprocessSource(options)

    # TODO: move FindAllParsers to engine as a class method?
    filter_query = getattr(options, 'parsers', '')
    self._parsers = putils.FindAllParsers(
        pre_obj=pre_obj, config=options, parser_filter_string=filter_query)
    self._parser_names = [parser.parser_name for parser in self._parsers['all']]

    self._PreprocessSetCollectionInformation(options, pre_obj)

    logging.debug(u'Preprocessing done.')

    if 'filestat' in self._parser_names:
      include_directory_stat = True
    else:
      include_directory_stat = False

    filter_file = getattr(options, 'file_filter', None)
    if filter_file:
      filter_find_specs = engine_utils.BuildFindSpecsFromFile(
          filter_file, pre_obj=pre_obj)
    else:
      filter_find_specs = None

    self._collector = self._engine.CreateCollector(
        include_directory_stat, vss_stores=self._vss_stores,
        filter_find_specs=filter_find_specs,
        resolver_context=self._resolver_context)

    self._DebugPrintCollector(options)

    logging.debug(u'Starting collection.')
    self._collector.Collect()
    logging.debug(u'Collection done.')

    extraction_worker = self._CreateExtractionWorker(0, options, pre_obj)

    logging.debug(u'Starting extraction worker.')
    extraction_worker.Run()
    logging.debug(u'Extraction worker done.')

    self._engine.SignalEndOfInputStorageQueue()

    output_module = getattr(options, 'output_module', None)
    if output_module:
      storage_writer = storage.BypassStorageWriter(
          storage_queue, self._storage_file_path,
          output_module_string=output_module, pre_obj=pre_obj)
    else:
      storage_writer = storage.StorageFileWriter(
          storage_queue, self._storage_file_path,
          buffer_size=self._buffer_size, pre_obj=pre_obj)

    logging.debug(u'Starting storage.')
    storage_writer.WriteEventObjects()
    logging.debug(u'Storage done.')

    self._resolver_context.Empty()

  # Note that this function is not called by the normal termination.
  def CleanUpAfterAbort(self):
    """Signals the tool to stop running nicely after an abort."""
    if self._single_process_mode and self._debug_mode:
      logging.warning(u'Running in debug mode, set up debugger.')
      pdb.post_mortem()
      return

    logging.warning(u'Stopping collector.')
    if self._collector:
      self._collector.SignalEndOfInput()

    logging.warning(u'Stopping storage.')
    self._engine.SignalEndOfInputStorageQueue()

    # Kill the collection process.
    if self._collection_process:
      logging.warning(u'Terminating the collection process.')
      self._collection_process.terminate()

    try:
      logging.warning(u'Waiting for workers to complete.')
      for worker_name, worker_process in self._worker_processes.iteritems():
        pid = worker_process.pid
        logging.warning(u'Waiting for worker: {0:s} [PID {1:d}]'.format(
            worker_name, pid))
        # Let's kill the process, different methods depending on the platform
        # used.
        if sys.platform.startswith('win'):
          import ctypes
          process_terminate = 1
          handle = ctypes.windll.kernel32.OpenProcess(
              process_terminate, False, pid)
          ctypes.windll.kernel32.TerminateProcess(handle, -1)
          ctypes.windll.kernel32.CloseHandle(handle)
        else:
          try:
            os.kill(pid, signal.SIGKILL)
          except OSError as exception:
            logging.error(
                u'Unable to kill process {0:d} with error: {1:s}'.format(
                    pid, exception))

        logging.warning(u'Worker: {0:d} CLOSED'.format(pid))

      logging.warning(u'Workers completed.')
      if hasattr(self, 'storage_process'):
        logging.warning(u'Waiting for storage.')
        self._storage_process.join()
        logging.warning(u'Storage ended.')

      logging.info(u'Exiting the tool.')
      # Sometimes the main process will be unresponsive.
      if not sys.platform.startswith('win'):
        os.kill(os.getpid(), signal.SIGKILL)

    except KeyboardInterrupt:
      logging.warning(u'Terminating all processes.')
      for process in self._worker_processes:
        process.terminate()

      logging.warning(u'Worker processes terminated.')
      if hasattr(self, 'storage_process'):
        self._storage_process.terminate()
        logging.warning(u'Storage terminated.')

      # Sometimes the main process will be unresponsive.
      if not sys.platform.startswith('win'):
        os.kill(os.getpid(), signal.SIGKILL)

  def GetSourceFileSystemSearcher(self):
    """Retrieves the file system searcher of the source.

    Returns:
      The file system searcher object (instance of dfvfs.FileSystemSearcher).
    """
    return self._engine.GetSourceFileSystemSearcher(
        resolver_context=self._resolver_context)

  def GetSourcePathSpec(self):
    """Retrieves the source path specification.

    Returns:
      The source path specification (instance of dfvfs.PathSpec).
    """
    return self._source_path_spec

  def ParseOptions(self, options, source_option):
    """Parses the options and initializes the front-end.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      source_option: the name of the source option.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    if not options:
      raise errors.BadConfigOption(u'Missing options.')

    self._source_path = getattr(options, source_option, None)
    if not self._source_path:
      raise errors.BadConfigOption(u'Missing source path.')

    try:
      self._source_path = unicode(self._source_path)
    except UnicodeDecodeError as exception:
      raise errors.BadConfigOption(
          u'Unable to convert source path to Unicode with error: {0:s}.'.format(
              exception))

    self._source_path = os.path.abspath(self._source_path)

    self._buffer_size = getattr(options, 'buffer_size', 0)
    if self._buffer_size:
      # TODO: turn this into a generic function that supports more size
      # suffixes both MB and MiB and also that does not allow m as a valid
      # indicator for MiB since m represents milli not Mega.
      try:
        if self._buffer_size[-1].lower() == 'm':
          self._buffer_size = int(self._buffer_size[:-1], 10)
          self._buffer_size *= self._BYTES_IN_A_MIB
        else:
          self._buffer_size = int(self._buffer_size, 10)
      except ValueError:
        raise errors.BadConfigOption(
            u'Invalid buffer size: {0:s}.'.format(self._buffer_size))

    self._filter_expression = getattr(options, 'filter', None)
    if self._filter_expression:
      self._filter_object = pfilter.GetMatcher(self._filter_expression)
      if not self._filter_object:
        raise errors.BadConfigOption(
            u'Invalid filter expression: {0:s}'.format(self._filter_expression))

    filter_file = getattr(options, 'file_filter', None)
    if filter_file and not os.path.isfile(filter_file):
      raise errors.BadConfigOption(
          u'No such collection filter file: {0:s}.'.format(filter_file))

    self._debug_mode = getattr(options, 'debug', False)

    timezone_string = getattr(options, 'timezone', None)
    if timezone_string:
      self._timezone = pytz.timezone(timezone_string)

    self._single_process_mode = getattr(
        options, 'single_process', False)

  def PreprocessSource(self, options):
    """Preprocesses the source.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Returns:
      The preprocessing object (instance of PreprocessObject).
    """
    pre_obj = None

    old_preprocess = getattr(options, 'old_preprocess', False)
    if old_preprocess and os.path.isfile(self._storage_file_path):
      # Check if the storage file contains a preprocessing object.
      try:
        with storage.StorageFile(
            self._storage_file_path, read_only=True) as store:
          storage_information = store.GetStorageInformation()
          if storage_information:
            logging.info(u'Using preprocessing information from a prior run.')
            pre_obj = storage_information[-1]
            self._preprocess = False
      except IOError:
        logging.warning(u'Storage file does not exist, running preprocess.')

    if not pre_obj:
      pre_obj = event.PreprocessObject()

    if self._preprocess and self._source_type in [
        self._SOURCE_TYPE_DIRECTORY, self._SOURCE_TYPE_STORAGE_MEDIA_IMAGE]:
      platform = getattr(options, 'os', None)
      try:
        self._engine.PreprocessSource(
            pre_obj, platform, resolver_context=self._resolver_context)
      except IOError as exception:
        logging.error(u'Unable to preprocess with error: {0:s}'.format(
            exception))
        return

    self._PreprocessSetTimezone(options, pre_obj)
    self._PreprocessSetParserFilter(options, pre_obj)

    return pre_obj

  def ProcessSource(self, options):
    """Processes the source.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are incorrect or not supported.
    """
    try:
      # TODO: move scanner into engine.
      self.ScanSource(options)
    except errors.FileSystemScannerError as exception:
      # TODO: make this a processing error.
      raise errors.BadConfigOption((
          u'Unable to scan for a supported filesystem with error: {0:s}.\n'
          u'Most likely the image format is not supported by the '
          u'tool.').format(exception))

    self.PrintOptions(options, self._source_path)

    if self._partition_offset is None:
      self._preprocess = False

    else:
      # If we're dealing with a storage media image always run pre-processing.
      self._preprocess = True

    self._CheckStorageFile(self._storage_file_path)

    # No need to multi process when we're only processing a single file.
    if self._source_type == self._SOURCE_TYPE_FILE:
      self._single_process_mode = True

    if self._single_process_mode:
      self._ProcessSourceSingleProcessMode(options)
    else:
      self._ProcessSourceMultiProcessMode(options)

  def ScanSource(self, options):
    """Scans the source path for volume and file systems.

    This functions sets the internal source path specification and source
    type values.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    partition_number = getattr(options, 'partition_number', None)
    if (partition_number is not None and
        isinstance(partition_number, basestring)):
      try:
        partition_number = int(partition_number, 10)
      except ValueError:
        logging.warning(u'Invalid partition number: {0:s}.'.format(
            partition_number))
        partition_number = None

    partition_offset = getattr(options, 'image_offset_bytes', None)
    if (partition_offset is not None and
        isinstance(partition_offset, basestring)):
      try:
        partition_offset = int(partition_offset, 10)
      except ValueError:
        logging.warning(u'Invalid image offset bytes: {0:s}.'.format(
            partition_offset))
        partition_offset = None

    if partition_offset is None and hasattr(options, 'image_offset'):
      image_offset = getattr(options, 'image_offset')
      bytes_per_sector = getattr(options, 'bytes_per_sector', 512)

      if isinstance(image_offset, basestring):
        try:
          image_offset = int(image_offset, 10)
        except ValueError:
          logging.warning(u'Invalid image offset: {0:s}.'.format(image_offset))
          image_offset = None

      if isinstance(bytes_per_sector, basestring):
        try:
          bytes_per_sector = int(bytes_per_sector, 10)
        except ValueError:
          logging.warning(u'Invalid bytes per sector: {0:s}.'.format(
              bytes_per_sector))
          bytes_per_sector = 512

      if image_offset:
        partition_offset = image_offset * bytes_per_sector

    vss_stores = getattr(options, 'vss_stores', None)
    if vss_stores:
      vss_stores = self._file_system_scanner.ParseVssStores(vss_stores)

    self._source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=self._source_path)

    # Note that os.path.isfile() can return false when source_path points
    # to a device file.
    if os.path.isdir(self._source_path):
      self._source_type = self._SOURCE_TYPE_DIRECTORY
      return

    scan_path_spec = self._source_path_spec
    path_spec = self._file_system_scanner.ScanForStorageMediaImage(
        scan_path_spec)
    if path_spec:
      scan_path_spec = path_spec

    # In case we did not find a storage media image type we keep looking
    # since the RAW storage media image type is detected by its content.

    while True:
      path_spec = self._file_system_scanner.ScanForVolumeSystem(scan_path_spec)
      if not path_spec:
        break

      scan_path_spec = path_spec

      if scan_path_spec.type_indicator in [
          dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION]:
        path_spec = self._GetVolumeTSKPartition(
            scan_path_spec, partition_number=partition_number,
            partition_offset=partition_offset)
        if not path_spec:
          break
        scan_path_spec = path_spec

      elif scan_path_spec.type_indicator in [
          dfvfs_definitions.TYPE_INDICATOR_VSHADOW]:
        path_spec = self._GetVolumeVssStoreIdentifiers(
            scan_path_spec, vss_stores=vss_stores)

        # Trace back to the parent volume path specification.
        scan_path_spec = scan_path_spec.parent
        break

    # In case we did not find a volume system type we keep looking
    # since we could be dealing with a storage media image that contains
    # a single volume.

    path_spec = self._file_system_scanner.ScanForFileSystem(scan_path_spec)
    if path_spec:
      self._source_path_spec = path_spec
      self._source_type = self._SOURCE_TYPE_STORAGE_MEDIA_IMAGE

      if self._partition_offset is None:
        self._partition_offset = 0

    else:
      if scan_path_spec.type_indicator in [
          dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION]:
        logging.warning(
            u'Unsupported file system falling back to single file mode.')

      self._source_type = self._SOURCE_TYPE_FILE

  def SetStorageFile(self, storage_file_path):
    """Sets the storage file path.

    Args:
      storage_file_path: The path of the storage file.
    """
    self._storage_file_path = storage_file_path

  def SetRunForeman(self, run_foreman=True):
    """Sets a flag indicating whether the frontend should monitor workers.

    Args:
      run_foreman: A boolean (defaults to true) that indicates whether or not
                   the frontend should start a foreman that monitors workers.
    """
    self._run_foreman = run_foreman

  def SetShowMemoryInformation(self, show_memory=True):
    """Sets a flag telling the worker monitor to show memory information.

    Args:
      show_memory: A boolean (defaults to True) that indicates whether or not
                   the foreman should include memory information as part of
                   the worker monitoring.
    """
    self._show_worker_memory_information = show_memory


class AnalysisFrontend(Frontend):
  """Class that implements an analysis front-end."""

  def __init__(self, input_reader, output_writer):
    """Initializes the front-end object.

    Args:
      input_reader: the input reader (instance of FrontendInputReader).
                    The default is None which indicates to use the stdin
                    input reader.
      output_writer: the output writer (instance of FrontendOutputWriter).
                     The default is None which indicates to use the stdout
                     output writer.
    """
    super(AnalysisFrontend, self).__init__(input_reader, output_writer)

    self._storage_file_path = None

  def AddStorageFileOptions(self, argument_group):
    """Adds the storage file options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup) or argument parser (instance of
                      argparse.ArgumentParser).
    """
    argument_group.add_argument(
        'storage_file', metavar='STORAGE_FILE', action='store', nargs='?',
        type=unicode, default=None, help='The path of the storage file.')

  def OpenStorageFile(self, read_only=True):
    """Opens the storage file.

    Args:
      read_only: Optional boolean value to indicate the storage file should
                 be opened in read-only mode. The default is True.

    Returns:
      The storage file object (instance of StorageFile).
    """
    return storage.StorageFile(self._storage_file_path, read_only=read_only)

  def ParseOptions(self, options):
    """Parses the options and initializes the front-end.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    if not options:
      raise errors.BadConfigOption(u'Missing options.')

    self._storage_file_path = getattr(options, 'storage_file', None)
    if not self._storage_file_path:
      raise errors.BadConfigOption(u'Missing storage file.')

    if not os.path.isfile(self._storage_file_path):
      raise errors.BadConfigOption(
          u'No such storage file {0:s}.'.format(self._storage_file_path))
