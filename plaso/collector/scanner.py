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
"""Scanner for file systems.

The file system scanner determines what input we're dealing with.
The following types of input are supported:
* a file that needs to be processed individually;
* a directory that needs to processed recursively;
* a file that contains a storage media image;
* a device file of a storage media image device.

The file system scanner determines the input type and scans for:
* supported types of storage media images
* supported types of volume systems
* supported types of file systems

If the files scanner cannot determine the best way to proceed
it will use the input reader and output writer to ask for external
input, e.g. directly from the user.
"""

import abc
import logging
import os
import sys

from dfvfs.analyzer import analyzer
from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.volume import tsk_volume_system
from dfvfs.volume import vshadow_volume_system

from plaso.lib import errors
from plaso.lib import timelib


class ScannerInputReader(object):
  """Class that implements the input reader interface for the scanner."""

  @abc.abstractmethod
  def Read(self):
    """Reads a string from the input.

    Returns:
      A string containing the input.
    """


class ScannerOutputWriter(object):
  """Class that implements the output writer interface for the scanner."""

  @abc.abstractmethod
  def Write(self, string):
    """Wtites a string to the output.

    Args:
      string: A string containing the output.
    """


class StdinScannerInputReader(object):
  """Class that implements a stdin input reader."""

  def Read(self):
    """Reads a string from the input.

    Returns:
      A string containing the input.
    """
    return sys.stdin.readline()


class StdoutScannerOutputWriter(object):
  """Class that implements a stdout output writer."""

  def Write(self, string):
    """Wtites a string to the output.

    Args:
      string: A string containing the output.
    """
    sys.stdout.write(string)


class FileSystemScanner(object):
  """Class that implements a file system scanner."""

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the file system scanner.

    Args:
      input_reader: the input reader (instance of ScannerInputReader).
                    The default is None which indicates to use the stdin
                    input reader.
      output_writer: the output writer (instance of ScannerOutputWriter).
                     The default is None which indicates to use the stdout
                     output writer.
    """
    super(FileSystemScanner, self).__init__()
    self._partition_number = None
    self._partition_offset = None
    self._vss_stores = None

    if input_reader:
      self._input_reader = input_reader
    else:
      self._input_reader = StdinScannerInputReader()

    if output_writer:
      self._output_writer = output_writer
    else:
      self._output_writer = StdoutScannerOutputWriter()

    self.is_storage_media_image = None
    self.partition_offset = None
    self.vss_stores = None

  def _GetNextLevelTSKPartionVolumeSystemPathSpec(self, source_path_spec):
    """Determines the next level volume system path specification.

    Args:
      source_path_spec: the source path specification (instance of
                        dfvfs.PathSpec).

    Returns:
      The next level volume system path specification (instance of
      dfvfs.PathSpec). If no next level is found the source path
      specification is returned.

    Raises:
      FileSystemScannerError: if the format of or within the source
                              is not supported.
      RuntimeError: if the volume for a specific identifier cannot be
                    retrieved.
    """
    volume_system_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TSK_PARTITION, location=u'/',
        parent=source_path_spec)

    volume_system = tsk_volume_system.TSKVolumeSystem()
    volume_system.Open(volume_system_path_spec)

    volume_identifiers = self._GetVolumeIdentifiers(volume_system)

    if not volume_identifiers:
      logging.info(u'No supported partitions found.')
      return source_path_spec

    if self._partition_number is not None:
      volume = volume_system.GetVolumeByIndex(self._partition_number)

      if volume:
        volume_extent = volume.extents[0]
        self.partition_offset = volume_extent.offset
        return path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_TSK_PARTITION,
            start_offset=volume_extent.offset, parent=source_path_spec)

      logging.warning(
        u'No such partition: {0:d}.'.format(self._partition_number))

    if self._partition_offset is not None:
      for volume in volume_system.volumes:
        volume_extent = volume.extents[0]
        if volume_extent.offset == self._partition_offset:
          self.partition_offset = volume_extent.offset
          return path_spec_factory.Factory.NewPathSpec(
              definitions.TYPE_INDICATOR_TSK_PARTITION,
              start_offset=volume_extent.offset, parent=source_path_spec)

      logging.warning(
        u'No such partition with offset: {0:d} (0x{0:08x}).'.format(
            self._partition_offset))
      self._partition_offset = None

    if len(volume_identifiers) == 1:
      volume = volume_system.GetVolumeByIdentifier(volume_identifiers[0])
      if not volume:
        raise RuntimeError(
            u'Unable to retieve volume by identifier: {0:s}'.format(
                volume_identifiers[0]))

      volume_extent = volume.extents[0]
      self.partition_offset = volume_extent.offset
      return path_spec_factory.Factory.NewPathSpec(
          definitions.TYPE_INDICATOR_TSK_PARTITION, location=u'/p1',
          parent=source_path_spec)

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
    self.partition_offset = volume_extent.offset
    return path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TSK_PARTITION, location=location,
        parent=source_path_spec)

  def _GetNextLevelVShadowVolumeSystemPathSpec(self, source_path_spec):
    """Determines the next level volume system path specification.

    Args:
      source_path_spec: the source path specification (instance of
                        dfvfs.PathSpec).

    Returns:
      The next level volume system path specification (instance of
      dfvfs.PathSpec). If no next level is found the source path
      specification is returned.

    Raises:
      FileSystemScannerError: if the format of or within the source
                              is not supported.
    """
    if source_path_spec.type_indicator == definitions.TYPE_INDICATOR_VSHADOW:
      raise errors.FileSystemScannerError(u'Unable to scan for VSS inside VSS.')

    volume_system_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_VSHADOW, location=u'/',
        parent=source_path_spec)

    volume_system = vshadow_volume_system.VShadowVolumeSystem()
    volume_system.Open(volume_system_path_spec)

    volume_identifiers = self._GetVolumeIdentifiers(volume_system)

    if not volume_identifiers:
      return source_path_spec

    try:
      self.vss_stores = self._GetVShadowIdentifiersFromUser(
          volume_system, volume_identifiers)
    except KeyboardInterrupt:
      raise errors.FileSystemScannerError(u'File system scan aborted.')

    return source_path_spec

  def _GetPartionIdentifierFromUser(self, volume_system, volume_identifiers):
    """Asks the user to provide the partitioned volume identifier.

    Args:
      volume_system: The volume system (instance of dfvfs.TSKVolumeSystem).
      volume_identifiers: List of allowed volume identifiers.
    """
    self._output_writer.Write(
        u'The following partitions were found:\n'
        u'Identifier\tOffset (in bytes)\tSize (in bytes)\n')

    for volume_identifier in volume_identifiers:
      volume = volume_system.GetVolumeByIdentifier(volume_identifier)
      if not volume:
        raise errors.FileSystemScannerError(
            u'Volume missing for identifier: {0:s}.'.format(
                volume_identifier))

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

  def _GetVShadowIdentifiersFromUser(self, volume_system, volume_identifiers):
    """Asks the user to provide the VSS volume identifiers.

    Args:
      volume_system: The volume system (instance of dfvfs.VShadowVolumeSystem).
      volume_identifiers: List of allowed volume identifiers.
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

    if self._vss_stores:
      if not set(self._vss_stores).difference(
          normalized_volume_identifiers):
        return self._vss_stores

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

      selected_volume_identifier = self._input_reader.Read()

      selected_volume_identifier = selected_volume_identifier.strip()
      if not selected_volume_identifier:
        break

      try:
        selected_volume_identifier = self._ParseVssStores(
            selected_volume_identifier)
      except errors.BadConfigOption:
        selected_volume_identifier = []

      if not set(selected_volume_identifier).difference(
          normalized_volume_identifiers):
        break

      self._output_writer.Write(
          u'\n'
          u'Unsupported VSS identifier(s), please try again or abort with '
          u'Ctrl^C.\n'
          u'\n')

    return selected_volume_identifier

  def _GetUpperLevelVolumeSystemPathSpec(self, source_path_spec):
    """Determines the upper level volume system path specification.

    Args:
      source_path_spec: the source path specification (instance of
                        dfvfs.PathSpec).

    Returns:
      The upper level volume system path specification (instance of
      dfvfs.PathSpec).

    Raises:
      FileSystemScannerError: if the format of or within the source
                              is not supported.
    """
    while True:
      type_indicators = analyzer.Analyzer.GetVolumeSystemTypeIndicators(
          source_path_spec)

      if not type_indicators:
        # No supported volume system found, we are at the upper level.
        return source_path_spec

      if len(type_indicators) > 1:
        raise errors.FileSystemScannerError(
            u'Unsupported source found more than one volume system types.')

      if type_indicators[0] == definitions.TYPE_INDICATOR_TSK_PARTITION:
        path_spec = self._GetNextLevelTSKPartionVolumeSystemPathSpec(
            source_path_spec)

      elif type_indicators[0] == definitions.TYPE_INDICATOR_VSHADOW:
        path_spec = self._GetNextLevelVShadowVolumeSystemPathSpec(
          source_path_spec)
        break

      else:
        raise errors.FileSystemScannerError((
            u'Unsupported source found unsupported volume system '
            u'type: {0:s}.').format(type_indicators[0]))

      source_path_spec = path_spec

    return path_spec

  def _GetVolumeIdentifiers(self, volume_system):
    """Retrieves the volume identifiers.

    Args:
      volume_system: The volume system (instance of dfvfs.VolumeSystem).

    Returns:
      A list containing the volume identifiers.
    """
    volume_identifiers = []
    for volume in volume_system.volumes:
      volume_identifier = getattr(volume, 'identifier', None)
      if volume_identifier:
        volume_identifiers.append(volume_identifier)

    return sorted(volume_identifiers)

  def _ParseVssStores(self, vss_stores):
    """Parses the user specified VSS stores stirng.

    Args:
      vss_stores: a string containing the VSS stores.
                  Where 1 represents the first store.

    Returns:
      The list of VSS stores.

    Raises:
      BadConfigOption: if the VSS stores option is invalid.
    """
    if not vss_stores:
      return []

    stores = []
    for vss_store_range in vss_stores.split(','):
      # Determine if the range is formatted as 1..3 otherwise it indicates
      # a single store number.
      if '..' in vss_store_range:
        first_store, last_store = vss_store_range.split('..')
        try:
          first_store = int(first_store, 10)
          last_store = int(last_store, 10)
        except ValueError:
          raise errors.BadConfigOption(
              u'Invalid VSS store range: {0:s}.'.format(vss_store_range))

        for store_number in range(first_store, last_store + 1):
          if store_number not in stores:
            stores.append(store_number)
      else:
        try:
          store_number = int(vss_store_range, 10)
        except ValueError:
          raise errors.BadConfigOption(
              u'Invalid VSS store range: {0:s}.'.format(vss_store_range))

        if store_number not in stores:
          stores.append(store_number)

    return sorted(stores)

  def Scan(self, source_path):
    """Scans the source path for a file system.

    Args:
      source_path: the source path.

    Returns:
      The base path specification (instance of dfvfs.PathSpec).

    Raises:
      FileSystemScannerError: if the source cannot be processed.
    """
    source_path = os.path.abspath(source_path)
    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=source_path)

    # Note that os.path.isfile() will return false when source_path points
    # to a device file.
    if os.path.isdir(source_path):
      self.is_storage_media_image = False
      return source_path_spec

    path_spec = source_path_spec
    type_indicators = analyzer.Analyzer.GetStorageMediaImageTypeIndicators(
        path_spec)

    if len(type_indicators) > 1:
      raise errors.FileSystemScannerError((
          u'Unsupported source: {0:s} found more than one storage media '
          u'image types.').format(source_path))

    if len(type_indicators) == 1:
      path_spec = path_spec_factory.Factory.NewPathSpec(
          type_indicators[0], parent=path_spec)

    # In case we did not find a storage media image type we keep looking
    # since the RAW storage media image type is detected by its content.

    path_spec = self._GetUpperLevelVolumeSystemPathSpec(path_spec)

    # In case we did not find a volume system type we keep looking
    # since we could be dealing with a storage media image that contains
    # a single volume.

    try:
      type_indicators = analyzer.Analyzer.GetFileSystemTypeIndicators(
          path_spec)
    except RuntimeError as exception:
      raise errors.FileSystemScannerError(
          u'Unable to process image, with error {:s}'.format(
              exception))

    if len(type_indicators) > 1:
      raise errors.FileSystemScannerError((
          u'Unsupported source: {0:s} found more than one file system '
          u'types.').format(source_path))

    if not type_indicators:
      self.is_storage_media_image = False
      return source_path_spec

    if type_indicators[0] != definitions.TYPE_INDICATOR_TSK:
      raise errors.FileSystemScannerError(
          u'Unsupported file system type: {0:s}.'.format(type_indicators[0]))

    self.is_storage_media_image = True
    if self.partition_offset is None:
      self.partition_offset = 0
    return path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=path_spec)

  def SetPartitionNumber(self, partition_number):
    """Sets the partition number.

    Args:
      partition_number: The partition number.
    """
    if isinstance(partition_number, basestring):
      try:
        partition_number = int(partition_number, 10)
      except ValueError:
        logging.warning(u'Invalid partition number: {0:s}.'.format(
            partition_number))
        return

    self._partition_number = partition_number

  def SetPartitionOffset(self, partition_offset):
    """Sets the partition offset.

    Args:
      partition_offset: The partition offset in bytes.
    """
    self._partition_offset = partition_offset

  def SetVssStores(self, vss_stores):
    """Sets the VSS stores.

    Args:
      vss_stores: a string containing the VSS stores.
                  Where 1 represents the first store.
    """
    self._vss_stores = self._ParseVssStores(vss_stores)
