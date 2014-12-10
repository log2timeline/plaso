#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
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
"""Generic collector that supports both file system and image files."""

import hashlib
import logging
import os

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.engine import queue
from plaso.lib import errors


class Collector(queue.ItemQueueProducer):
  """Class that implements a collector object."""

  def __init__(
      self, process_queue, source_path, source_path_spec,
      resolver_context=None):
    """Initializes the collector object.

       The collector discovers all the files that need to be processed by
       the workers. Once a file is discovered it is added to the process queue
       as a path specification (instance of dfvfs.PathSpec).

    Args:
      process_queue: The process queue (instance of Queue). This queue contains
                     the file entries that need to be processed.
      source_path: Path of the source file or directory.
      source_path_spec: The source path specification (instance of
                        dfvfs.PathSpec) as determined by the file system
                        scanner. The default is None.
      resolver_context: Optional resolver context (instance of dfvfs.Context).
                        The default is None.
    """
    super(Collector, self).__init__(process_queue)
    self._filter_find_specs = None
    self._fs_collector = FileSystemCollector(process_queue)
    self._resolver_context = resolver_context
    # TODO: remove the need to pass source_path
    self._source_path = os.path.abspath(source_path)
    self._source_path_spec = source_path_spec
    self._vss_stores = None

  def __enter__(self):
    """Enters a with statement."""
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Exits a with statement."""
    return

  def _ProcessImage(self, volume_path_spec, find_specs=None):
    """Processes a volume within a storage media image.

    Args:
      volume_path_spec: The path specification of the volume containing
                        the file system.
      find_specs: Optional list of find specifications (instances of
                  dfvfs.FindSpec). The default is None.
    """
    if find_specs:
      logging.debug(u'Collecting from image file: {0:s} with filter'.format(
          self._source_path))
    else:
      logging.debug(u'Collecting from image file: {0:s}'.format(
          self._source_path))

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=volume_path_spec)

    try:
      file_system = path_spec_resolver.Resolver.OpenFileSystem(
          path_spec, resolver_context=self._resolver_context)
    except IOError as exception:
      logging.error(
          u'Unable to open file system with error: {0:s}'.format(exception))
      return

    try:
      self._fs_collector.Collect(
          file_system, path_spec, find_specs=find_specs)
    except (dfvfs_errors.AccessError, dfvfs_errors.BackEndError) as exception:
      logging.warning(u'{0:s}'.format(exception))

      if find_specs:
        logging.debug(u'Collection from image with filter FAILED.')
      else:
        logging.debug(u'Collection from image FAILED.')
      return

    if self._abort:
      return

    if self._vss_stores:
      self._ProcessVSS(volume_path_spec, find_specs=find_specs)

    if find_specs:
      logging.debug(u'Collection from image with filter COMPLETED.')
    else:
      logging.debug(u'Collection from image COMPLETED.')

  def _ProcessVSS(self, volume_path_spec, find_specs=None):
    """Processes a VSS volume within a storage media image.

    Args:
      volume_path_spec: The path specification of the volume containing
                        the file system.
      find_specs: Optional list of find specifications (instances of
                  dfvfs.FindSpec). The default is None.
    """
    logging.info(u'Processing VSS.')

    vss_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_VSHADOW, location=u'/',
        parent=volume_path_spec)

    vss_file_entry = path_spec_resolver.Resolver.OpenFileEntry(
        vss_path_spec, resolver_context=self._resolver_context)

    number_of_vss = vss_file_entry.number_of_sub_file_entries

    # In plaso 1 represents the first store index in dfvfs and pyvshadow 0
    # represents the first store index so 1 is subtracted.
    vss_store_range = [store_nr - 1 for store_nr in self._vss_stores]

    for store_index in vss_store_range:
      if self._abort:
        return

      if find_specs:
        logging.info((
            u'Collecting from VSS volume: {0:d} out of: {1:d} '
            u'with filter').format(store_index + 1, number_of_vss))
      else:
        logging.info(u'Collecting from VSS volume: {0:d} out of: {1:d}'.format(
            store_index + 1, number_of_vss))

      vss_path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_VSHADOW, store_index=store_index,
          parent=volume_path_spec)
      path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
          parent=vss_path_spec)

      file_system = path_spec_resolver.Resolver.OpenFileSystem(
          path_spec, resolver_context=self._resolver_context)

      try:
        self._fs_collector.Collect(
            file_system, path_spec, find_specs=find_specs)
      except (dfvfs_errors.AccessError, dfvfs_errors.BackEndError) as exception:
        logging.warning(u'{0:s}'.format(exception))

        if find_specs:
          logging.debug(
              u'Collection from VSS store: {0:d} with filter FAILED.'.format(
                  store_index + 1))
        else:
          logging.debug(u'Collection from VSS store: {0:d} FAILED.'.format(
              store_index + 1))
        return

      if find_specs:
        logging.debug(
            u'Collection from VSS store: {0:d} with filter COMPLETED.'.format(
                store_index + 1))
      else:
        logging.debug(u'Collection from VSS store: {0:d} COMPLETED.'.format(
            store_index + 1))

  def Collect(self):
    """Collects files from the source."""
    source_file_entry = path_spec_resolver.Resolver.OpenFileEntry(
        self._source_path_spec, resolver_context=self._resolver_context)

    if not source_file_entry:
      logging.warning(u'No files to collect.')
      self.SignalEndOfInput()
      return

    if (not source_file_entry.IsDirectory() and
        not source_file_entry.IsFile() and
        not source_file_entry.IsDevice()):
      raise errors.CollectorError(
          u'Source path: {0:s} not a device, file or directory.'.format(
              self._source_path))

    type_indicator = self._source_path_spec.type_indicator
    if type_indicator == dfvfs_definitions.TYPE_INDICATOR_OS:
      if source_file_entry.IsFile():
        self.ProduceItem(self._source_path_spec)

      else:
        file_system = path_spec_resolver.Resolver.OpenFileSystem(
            self._source_path_spec, resolver_context=self._resolver_context)

        try:
          self._fs_collector.Collect(
              file_system, self._source_path_spec,
              find_specs=self._filter_find_specs)
        except (dfvfs_errors.AccessError,
                dfvfs_errors.BackEndError) as exception:
          logging.warning(u'{0:s}'.format(exception))

    else:
      self._ProcessImage(
          self._source_path_spec.parent, find_specs=self._filter_find_specs)

    self.SignalEndOfInput()

  def SetCollectDirectoryMetadata(self, collect_directory_metadata):
    """Sets the collect directory metadata flag.

    Args:
      collect_directory_metadata: Boolean value to indicate to collect
                                  directory metadata.
    """
    self._fs_collector.SetCollectDirectoryMetadata(collect_directory_metadata)

  def SetFilter(self, filter_find_specs):
    """Sets the collection filter find specifications.

    Args:
      filter_find_specs: List of filter find specifications (instances of
                         dfvfs.FindSpec).
    """
    self._filter_find_specs = filter_find_specs

  def SetVssInformation(self, vss_stores):
    """Sets the Volume Shadow Snapshots (VSS) information.

       This function will enable VSS collection.

    Args:
      vss_stores: The range of VSS stores to include in the collection,
                  where 1 represents the first store.
    """
    self._vss_stores = vss_stores

  def SignalAbort(self):
    """Signals the producer to abort."""
    super(Collector, self).SignalAbort()
    self._fs_collector.SignalAbort()


class FileSystemCollector(queue.ItemQueueProducer):
  """Class that implements a file system collector object."""

  def __init__(self, process_queue):
    """Initializes the collector object.

       The collector discovers all the files that need to be processed by
       the workers. Once a file is discovered it is added to the process queue
       as a path specification (instance of dfvfs.PathSpec).

    Args:
      process_queue: The process queue (instance of Queue). This queue contains
                     the file entries that need to be processed.
    """
    super(FileSystemCollector, self).__init__(process_queue)
    self._collect_directory_metadata = True
    self._duplicate_file_check = False
    self._hashlist = {}

    self.number_of_file_entries = 0

  def __enter__(self):
    """Enters a with statement."""
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Exits a with statement."""
    return

  def _CalculateNTFSTimeHash(self, file_entry):
    """Return a hash value calculated from a NTFS file's metadata.

    Args:
      file_entry: The file entry (instance of TSKFileEntry).

    Returns:
      A hash value (string) that can be used to determine if a file's timestamp
    value has changed.
    """
    stat_object = file_entry.GetStat()
    ret_hash = hashlib.md5()

    ret_hash.update('atime:{0:d}.{1:d}'.format(
        getattr(stat_object, 'atime', 0),
        getattr(stat_object, 'atime_nano', 0)))

    ret_hash.update('crtime:{0:d}.{1:d}'.format(
        getattr(stat_object, 'crtime', 0),
        getattr(stat_object, 'crtime_nano', 0)))

    ret_hash.update('mtime:{0:d}.{1:d}'.format(
        getattr(stat_object, 'mtime', 0),
        getattr(stat_object, 'mtime_nano', 0)))

    ret_hash.update('ctime:{0:d}.{1:d}'.format(
        getattr(stat_object, 'ctime', 0),
        getattr(stat_object, 'ctime_nano', 0)))

    return ret_hash.hexdigest()

  def _ProcessDirectory(self, file_entry):
    """Processes a directory and extract its metadata if necessary."""
    # Need to do a breadth-first search otherwise we'll hit the Python
    # maximum recursion depth.
    sub_directories = []

    for sub_file_entry in file_entry.sub_file_entries:
      if self._abort:
        return

      try:
        if not sub_file_entry.IsAllocated() or sub_file_entry.IsLink():
          continue
      except dfvfs_errors.BackEndError as exception:
        logging.warning(
            u'Unable to process file: {0:s} with error: {1:s}'.format(
                sub_file_entry.path_spec.comparable.replace(
                    u'\n', u';'), exception))
        continue

      # For TSK-based file entries only, ignore the virtual /$OrphanFiles
      # directory.
      if sub_file_entry.type_indicator == dfvfs_definitions.TYPE_INDICATOR_TSK:
        if file_entry.IsRoot() and sub_file_entry.name == u'$OrphanFiles':
          continue

      if sub_file_entry.IsDirectory():
        # This check is here to improve performance by not producing
        # path specifications that don't get processed.
        if self._collect_directory_metadata:
          self.ProduceItem(sub_file_entry.path_spec)
          self.number_of_file_entries += 1

        sub_directories.append(sub_file_entry)

      elif sub_file_entry.IsFile():
        # If we are dealing with a VSS we want to calculate a hash
        # value based on available timestamps and compare that to previously
        # calculated hash values, and only include the file into the queue if
        # the hash does not match.
        if self._duplicate_file_check:
          hash_value = self._CalculateNTFSTimeHash(sub_file_entry)

          inode = getattr(sub_file_entry.path_spec, 'inode', 0)
          if inode in self._hashlist:
            if hash_value in self._hashlist[inode]:
              continue

          self._hashlist.setdefault(inode, []).append(hash_value)

        self.ProduceItem(sub_file_entry.path_spec)
        self.number_of_file_entries += 1

    for sub_file_entry in sub_directories:
      if self._abort:
        return

      try:
        self._ProcessDirectory(sub_file_entry)
      except (dfvfs_errors.AccessError, dfvfs_errors.BackEndError) as exception:
        logging.warning(u'{0:s}'.format(exception))

  def Collect(self, file_system, path_spec, find_specs=None):
    """Collects files from the file system.

    Args:
      file_system: The file system (instance of dfvfs.FileSystem).
      path_spec: The path specification (instance of dfvfs.PathSpec).
      find_specs: Optional list of find specifications (instances of
                  dfvfs.FindSpec). The default is None.
    """
    if find_specs:
      searcher = file_system_searcher.FileSystemSearcher(file_system, path_spec)

      for path_spec in searcher.Find(find_specs=find_specs):
        if self._abort:
          return

        self.ProduceItem(path_spec)
        self.number_of_file_entries += 1

    else:
      file_entry = file_system.GetFileEntryByPathSpec(path_spec)

      self._ProcessDirectory(file_entry)

  def SetCollectDirectoryMetadata(self, collect_directory_metadata):
    """Sets the collect directory metadata flag.

    Args:
      collect_directory_metadata: Boolean value to indicate to collect
                                  directory metadata.
    """
    self._collect_directory_metadata = collect_directory_metadata
