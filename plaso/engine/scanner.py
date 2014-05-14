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

import logging

from dfvfs.analyzer import analyzer
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.lib import errors


class FileSystemScanner(object):
  """Class that implements a file system scanner."""

  def GetVolumeIdentifiers(self, volume_system):
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

  def ParseVssStores(self, vss_stores):
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

  def ScanForFileSystem(self, source_path_spec):
    """Scans the path specification for a supported file system format.

    Args:
      source_path_spec: the source path specification (instance of
                        dfvfs.PathSpec).

    Returns:
      The file system path specification (instance of dfvfs.PathSpec) or None
      if no supported file system type was found.

    Raises:
      FileSystemScannerError: if the source cannot be processed.
    """
    try:
      type_indicators = analyzer.Analyzer.GetFileSystemTypeIndicators(
          source_path_spec)
    except RuntimeError as exception:
      raise errors.FileSystemScannerError(
          u'Unable to process image with error {0:s}'.format(exception))

    if not type_indicators:
      return

    logging.debug(u'Found file system type indicators: {0!s}'.format(
        type_indicators))

    if len(type_indicators) > 1:
      raise errors.FileSystemScannerError(
          u'Unsupported source found more than one file system types.')

    if type_indicators[0] != dfvfs_definitions.TYPE_INDICATOR_TSK:
      raise errors.FileSystemScannerError(
          u'Unsupported file system type: {0:s}.'.format(type_indicators[0]))

    return path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=source_path_spec)

  def ScanForVolumeSystem(self, source_path_spec):
    """Scans the path specification for a supported volume system format.

    Args:
      source_path_spec: the source path specification (instance of
                        dfvfs.PathSpec).

    Returns:
      The volume system path specification (instance of dfvfs.PathSpec) or
      None if no supported volume system type was found.

    Raises:
      FileSystemScannerError: if the source cannot be processed.
    """
    # Do not scan for VSS in VSS.
    if source_path_spec.type_indicator in [
        dfvfs_definitions.TYPE_INDICATOR_VSHADOW]:
      return

    type_indicators = analyzer.Analyzer.GetVolumeSystemTypeIndicators(
        source_path_spec)

    if not type_indicators:
      return

    logging.debug(u'Found volume system type indicators: {0!s}'.format(
        type_indicators))

    if len(type_indicators) > 1:
      raise errors.FileSystemScannerError(
          u'Unsupported source found more than one volume system types.')

    if type_indicators[0] == dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION:
      path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION, location=u'/',
          parent=source_path_spec)

    elif type_indicators[0] == dfvfs_definitions.TYPE_INDICATOR_VSHADOW:
      path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_VSHADOW, location=u'/',
          parent=source_path_spec)

    else:
      raise errors.FileSystemScannerError(
          u'Unsupported volume system type: {0:s}.'.format(type_indicators[0]))

    return path_spec

  def ScanForStorageMediaImage(self, source_path_spec):
    """Scans the path specification for a supported storage media image format.

    Args:
      source_path_spec: the source path specification (instance of
                        dfvfs.PathSpec).

    Returns:
      The storage media image path specification (instance of dfvfs.PathSpec)
      or None if no supported storage media image type was found.

    Raises:
      FileSystemScannerError: if the source cannot be processed.
    """
    type_indicators = analyzer.Analyzer.GetStorageMediaImageTypeIndicators(
        source_path_spec)

    if not type_indicators:
      return

    logging.debug(u'Found storage media image type indicators: {0!s}'.format(
        type_indicators))

    if len(type_indicators) > 1:
      raise errors.FileSystemScannerError(
          u'Unsupported source found more than one storage media image types.')

    return path_spec_factory.Factory.NewPathSpec(
        type_indicators[0], parent=source_path_spec)
