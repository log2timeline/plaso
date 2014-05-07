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

from plaso.lib import errors
from plaso.lib import queue
from plaso.lib import utils
from plaso.parsers import filestat


# TODO: refactor.
def _SendContainerToStorage(file_entry, storage_queue_producer):
  """Read events from a event container and send them to storage.

  Args:
    file_entry: The file entry object (instance of dfvfs.FileEntry).
    storage_queue_producer: the storage queue producer (instance of
                            EventObjectQueueProducer).
  """
  stat_object = file_entry.GetStat()

  for event_object in filestat.StatEvents.GetEventsFromStat(stat_object):
    # TODO: dfVFS refactor: move display name to output since the path
    # specification contains the full information.
    event_object.display_name = u'{:s}:{:s}'.format(
        file_entry.path_spec.type_indicator, file_entry.name)

    event_object.filename = file_entry.name
    event_object.pathspec = file_entry.path_spec
    event_object.parser = u'FileStatParser'
    event_object.inode = utils.GetInodeValue(stat_object.ino)

    storage_queue_producer.ProduceEventObject(event_object)


class Collector(queue.PathSpecQueueProducer):
  """Class that implements a collector object."""

  def __init__(
      self, process_queue, storage_queue_producer, source_path,
      source_path_spec, resolver_context):
    """Initializes the collector object.

       The collector discovers all the files that need to be processed by
       the workers. Once a file is discovered it added to the process queue
       as a path specification (instance of dfvfs.PathSpec).

    Args:
      process_queue: The files processing queue (instance of Queue).
      storage_queue_producer: the storage queue producer (instance of
                              EventObjectQueueProducer).
      source_path: Path of the source file or directory.
      source_path_spec: The source path specification (instance of
                        dfvfs.PathSpec) as determined by the file system
                        scanner. The default is None.
      resolver_context: The resolver context (instance of dfvfs.Context).
    """
    super(Collector, self).__init__(process_queue)
    self._filter_file_path = None
    self._hashlist = None
    self._pre_obj = None
    self._process_vss = None
    self._resolver_context = resolver_context
    self._storage_queue_producer = storage_queue_producer
    # TODO: remove the need to pass source_path
    self._source_path = os.path.abspath(source_path)
    self._source_path_spec = source_path_spec
    self._vss_stores = None
    self.collect_directory_metadata = True

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

    ret_hash.update('atime:{0}.{1}'.format(
        getattr(stat_object, 'atime', 0),
        getattr(stat_object, 'atime_nano', 0)))

    ret_hash.update('crtime:{0}.{1}'.format(
        getattr(stat_object, 'crtime', 0),
        getattr(stat_object, 'crtime_nano', 0)))

    ret_hash.update('mtime:{0}.{1}'.format(
        getattr(stat_object, 'mtime', 0),
        getattr(stat_object, 'mtime_nano', 0)))

    ret_hash.update('ctime:{0}.{1}'.format(
        getattr(stat_object, 'ctime', 0),
        getattr(stat_object, 'ctime_nano', 0)))

    return ret_hash.hexdigest()

  def _ProcessDirectory(self, file_entry):
    """Processes a directory and extract its metadata if necessary."""
    # Need to do a breadth-first search otherwise we'll hit the Python
    # maximum recursion depth.
    sub_directories = []

    for sub_file_entry in file_entry.sub_file_entries:
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
        if self.collect_directory_metadata:
          # TODO: solve this differently by putting the path specification
          # on the queue and have the filestat parser just extract the metadata.
          # self.ProducePathSpec(sub_file_entry.path_spec)
          _SendContainerToStorage(file_entry, self._storage_queue_producer)

        sub_directories.append(sub_file_entry)

      elif sub_file_entry.IsFile():
        # If we are dealing with a VSS we want to calculate a hash
        # value based on available timestamps and compare that to previously
        # calculated hash values, and only include the file into the queue if
        # the hash does not match.
        if self._process_vss:
          hash_value = self._CalculateNTFSTimeHash(sub_file_entry)

          inode = getattr(sub_file_entry.path_spec, 'inode', 0)
          if inode in self._hashlist:
            if hash_value in self._hashlist[inode]:
              continue

          self._hashlist.setdefault(inode, []).append(hash_value)

        self.ProducePathSpec(sub_file_entry.path_spec)

    for sub_file_entry in sub_directories:
      try:
        self._ProcessDirectory(sub_file_entry)
      except (dfvfs_errors.AccessError, dfvfs_errors.BackEndError) as exception:
        logging.warning(u'{0:s}'.format(exception))

  def _ProcessFileSystemWithFilter(self):
    """Processes the source path based on the collection filter."""
    find_specs = BuildFindSpecsFromFile(self._filter_file_path)

    file_system = path_spec_resolver.Resolver.OpenFileSystem(
        self._source_path_spec)
    searcher = file_system_searcher.FileSystemSearcher(
        file_system, self._source_path_spec)

    for path_spec in searcher.Find(find_specs=find_specs):
      self.ProducePathSpec(path_spec)

  def _ProcessImage(self, volume_path_spec):
    """Processes a volume within a storage media image.

    Args:
      volume_path_spec: The path specification of the volume containing
                        the file system.
    """
    logging.debug(u'Collecting from image file: {0:s}'.format(
        self._source_path))

    if self._process_vss:
      self._hashlist = {}

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=volume_path_spec)

    try:
      root_file_entry = path_spec_resolver.Resolver.OpenFileEntry(
          path_spec, resolver_context=self._resolver_context)
    except IOError as exception:
      logging.error((
          u'Unable to read file system in storage media image with error: '
          u'{0:s}').format(exception))
      return

    try:
      self._ProcessDirectory(root_file_entry)
    except (dfvfs_errors.AccessError, dfvfs_errors.BackEndError) as exception:
      logging.warning(u'{0:s}'.format(exception))
      logging.debug(u'Collection from image ABORTED.')
      return

    if self._process_vss:
      logging.info(u'Collecting from VSS.')

      vss_path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_VSHADOW, location=u'/',
          parent=volume_path_spec)

      vss_file_entry = path_spec_resolver.Resolver.OpenFileEntry(
          vss_path_spec, resolver_context=self._resolver_context)

      number_of_vss = vss_file_entry.number_of_sub_file_entries
      if self._vss_stores:
        vss_store_range = [store_nr - 1 for store_nr in self._vss_stores]
      else:
        vss_store_range = range(0, number_of_vss)

      for store_index in vss_store_range:
        logging.info(u'Collecting from VSS volume: {0:d} out of: {1:d}'.format(
            store_index + 1, number_of_vss))
        self._ProcessVss(volume_path_spec, store_index)

    logging.debug(u'Collection from image COMPLETED.')

  def _ProcessImageWithFilter(self, volume_path_spec):
    """Processes a volume within an image with the collection filter.

    Args:
      volume_path_spec: The path specification of the volume containing
                        the file system.
    """
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=volume_path_spec)

    find_specs = BuildFindSpecsFromFile(self._filter_file_path)

    file_system = path_spec_resolver.Resolver.OpenFileSystem(path_spec)
    searcher = file_system_searcher.FileSystemSearcher(
        file_system, volume_path_spec)

    for path_spec in searcher.Find(find_specs=find_specs):
      self.ProducePathSpec(path_spec)

    if self._process_vss:
      logging.debug(u'Searching for VSS')

      vss_path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_VSHADOW, location=u'/',
          parent=volume_path_spec)

      vss_file_entry = path_spec_resolver.Resolver.OpenFileEntry(
          vss_path_spec, resolver_context=self._resolver_context)

      number_of_vss = vss_file_entry.number_of_sub_file_entries

      if not self._vss_stores:
        list_of_vss_stores = range(0, number_of_vss)
      else:
        list_of_vss_stores = []

        for store_index in self._vss_stores:
          if store_index > 0 and store_index <= number_of_vss:
            # In plaso 1 represents the first store index in
            # pyvshadow 0 represents the first store index so 1 is subtracted.
            list_of_vss_stores.append(store_index - 1)

      for store_index in list_of_vss_stores:
        logging.info(
            u'Collecting from VSS volume: {0:d} out of: {1:d}'.format(
                store_index + 1, number_of_vss))

        vss_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_VSHADOW, store_index=store_index,
            parent=volume_path_spec)
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
            parent=vss_path_spec)

        file_system = path_spec_resolver.Resolver.OpenFileSystem(path_spec)
        searcher = file_system_searcher.FileSystemSearcher(
            file_system, vss_path_spec)

        for path_spec in searcher.Find(find_specs=find_specs):
          self.ProducePathSpec(path_spec)

    logging.debug(u'Targeted Image Collector - Done.')

  def _ProcessVss(self, volume_path_spec, store_index):
    """Processes a Volume Shadow Snapshot (VSS) in the image.

    Args:
      volume_path_spec: The path specification of the volume containing
                        the VSS.
      store_index: The VSS store index number.
    """
    logging.debug(u'Collecting from VSS store {0:d}'.format(store_index))

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_VSHADOW, store_index=store_index,
        parent=volume_path_spec)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/', parent=path_spec)

    root_file_entry = path_spec_resolver.Resolver.OpenFileEntry(
        path_spec, resolver_context=self._resolver_context)

    try:
      self._ProcessDirectory(root_file_entry)
    except (dfvfs_errors.AccessError, dfvfs_errors.BackEndError) as exception:
      logging.warning(u'{0:s}'.format(exception))
      logging.debug(
          u'Collection from VSS store: {0:d} ABORTED.'.format(store_index))
      return

    logging.debug(
        u'Collection from VSS store: {0:d} COMPLETED.'.format(store_index))

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
      if self._filter_file_path:
        self._ProcessFileSystemWithFilter()

      elif source_file_entry.IsDirectory():
        try:
          self._ProcessDirectory(source_file_entry)
        except (dfvfs_errors.AccessError,
                dfvfs_errors.BackEndError) as exception:
          logging.warning(u'{0:s}'.format(exception))

      else:
        self.ProducePathSpec(self._source_path_spec)

    else:
      if self._filter_file_path:
        self._ProcessImageWithFilter(self._source_path_spec.parent)
      else:
        self._ProcessImage(self._source_path_spec.parent)

    self.SignalEndOfInput()

  def SetFilter(self, filter_file_path, pre_obj):
    """Sets the collection filter.

    Args:
      filter_file_path: The path of the filter file.
      pre_obj: The preprocessor object (instance of PreprocessObject).
    """
    self._filter_file_path = filter_file_path
    self._pre_obj = pre_obj

  def SetVssInformation(self, vss_stores=None):
    """Sets the Volume Shadow Snapshots (VSS) information.

       This function will enable VSS collection.

    Args:
      vss_stores: Optional range of VSS stores to include in the collection.
                  Where 1 represents the first store. The default is None.
    """
    self._process_vss = True
    self._vss_stores = vss_stores


def BuildFindSpecsFromFile(filter_file_path):
  """Returns a list of find specification from a filter file."""
  find_specs = []

  with open(filter_file_path, 'rb') as file_object:
    for line in file_object:
      line = line.strip()
      if line.startswith(u'#'):
        continue

      if not line.startswith(u'/'):
        logging.warning((
            u'The filter string must be defined as an abolute path: '
            u'{0:s}').format(line))
        continue

      _, _, file_path = line.rstrip().rpartition(u'/')
      if not file_path:
        logging.warning(
            u'Unable to parse the filter string: {0:s}'.format(line))
        continue

      # Convert the filter paths into a list of path segments and strip
      # the root path segment.
      path_segments = line.split(u'/')
      path_segments.pop(0)

      find_specs.append(file_system_searcher.FindSpec(
          location_regex=path_segments, case_sensitive=False))

  return find_specs
