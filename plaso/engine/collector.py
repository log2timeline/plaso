# -*- coding: utf-8 -*-
"""Generic collector that supports both file system and image files."""

import copy
import hashlib
import logging

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.engine import plaso_queue
from plaso.lib import definitions


class Collector(plaso_queue.ItemQueueProducer):
  """Class that implements a collector object."""

  def __init__(self, path_spec_queue, resolver_context=None):
    """Initializes the collector object.

       The collector discovers all the files that need to be processed by
       the workers. Once a file is discovered it is added to the process queue
       as a path specification (instance of dfvfs.PathSpec).

    Args:
      path_spec_queue: the path specification queue (instance of Queue).
                       This queue contains path specifications (instances
                       of dfvfs.PathSpec) of the file entries that need
                       to be processed.
      resolver_context: optional resolver context (instance of dfvfs.Context).
    """
    super(Collector, self).__init__(path_spec_queue)
    self._filter_find_specs = None
    self._fs_collector = FileSystemCollector(path_spec_queue)
    self._resolver_context = resolver_context

    # Attributes that contain the current status of the collector.
    self._status = definitions.PROCESSING_STATUS_INITIALIZED

  def _ProcessFileSystem(self, path_spec, find_specs=None):
    """Processes a file system within a storage media image.

    Args:
      path_spec: the path specification of the root of the file system.
      find_specs: optional list of find specifications (instances of
                  dfvfs.FindSpec).
    """
    try:
      file_system = path_spec_resolver.Resolver.OpenFileSystem(
          path_spec, resolver_context=self._resolver_context)
    except (
        dfvfs_errors.AccessError, dfvfs_errors.BackEndError,
        dfvfs_errors.PathSpecError) as exception:
      logging.error(
          u'Unable to open file system with error: {0:s}'.format(exception))
      return

    try:
      self._fs_collector.Collect(file_system, path_spec, find_specs=find_specs)

    except (
        dfvfs_errors.AccessError, dfvfs_errors.BackEndError,
        dfvfs_errors.PathSpecError) as exception:
      logging.warning(u'{0:s}'.format(exception))

    finally:
      file_system.Close()

  def _ProcessPathSpec(self, path_spec, find_specs=None):
    """Processes a specific path specification.

    Args:
      path_spec: the path specification (instance of dfvfs.path.PathSpec)
                 to process.
      find_specs: optional list of find specifications (instances of
                  dfvfs.FindSpec).
    """
    try:
      file_entry = path_spec_resolver.Resolver.OpenFileEntry(
          path_spec, resolver_context=self._resolver_context)
    except (
        dfvfs_errors.AccessError, dfvfs_errors.BackEndError,
        dfvfs_errors.PathSpecError) as exception:
      logging.error(
          u'Unable to open file entry with error: {0:s}'.format(exception))
      return

    if not file_entry:
      logging.warning(u'Unable to open: {0:s}'.format(path_spec.comparable))
      return

    if (not file_entry.IsDirectory() and not file_entry.IsFile() and
        not file_entry.IsDevice()):
      logging.warning((
          u'Source path specification not a device, file or directory.\n'
          u'{0:s}').format(path_spec.comparable))
      return

    if file_entry.IsFile():
      self.ProduceItem(path_spec)

    else:
      self._ProcessFileSystem(path_spec, find_specs=find_specs)

  def Collect(self, source_path_specs):
    """Collects file entry path specifications.

    Args:
      source_path_specs: list of path specifications (instances of
                         dfvfs.PathSpec) to collect from.
    """
    if not source_path_specs:
      logging.warning(u'No files to collect.')
      return

    for source_path_spec in source_path_specs:
      if self._abort:
        break

      self._status = definitions.PROCESSING_STATUS_RUNNING
      self._ProcessPathSpec(
          source_path_spec, find_specs=self._filter_find_specs)

    if self._abort:
      self._status = definitions.PROCESSING_STATUS_ABORTED
    else:
      self._status = definitions.PROCESSING_STATUS_COMPLETED

  def GetStatus(self):
    """Returns a dictionary containing the status."""
    produced_number_of_path_specs = (
        self.number_of_produced_items +
        self._fs_collector.number_of_produced_items)

    return {
        u'processing_status': self._status,
        u'produced_number_of_path_specs': produced_number_of_path_specs,
        u'path_spec_queue_port': getattr(self._queue, u'port', None),
        u'type': definitions.PROCESS_TYPE_COLLECTOR}

  def SetCollectDirectoryMetadata(self, collect_directory_metadata):
    """Sets the collect directory metadata flag.

    Args:
      collect_directory_metadata: boolean value to indicate to collect
                                  directory metadata.
    """
    self._fs_collector.SetCollectDirectoryMetadata(collect_directory_metadata)

  def SetFilter(self, filter_find_specs):
    """Sets the collection filter find specifications.

    Args:
      filter_find_specs: list of filter find specifications (instances of
                         dfvfs.FindSpec).
    """
    self._filter_find_specs = filter_find_specs

  def SignalAbort(self):
    """Signals the collector to abort."""
    self._fs_collector.SignalAbort()
    super(Collector, self).SignalAbort()


class FileSystemCollector(plaso_queue.ItemQueueProducer):
  """Class that implements a file system collector object."""

  def __init__(self, path_spec_queue, resolver_context=None):
    """Initializes the collector object.

       The collector discovers all the files that need to be processed by
       the workers. Once a file is discovered it is added to the process queue
       as a path specification (instance of dfvfs.PathSpec).

    Args:
      path_spec_queue: the path specification queue (instance of Queue).
                       This queue contains path specifications (instances
                       of dfvfs.PathSpec) of the file entries that need
                       to be processed.
      resolver_context: optional resolver context (instance of dfvfs.Context).
    """
    super(FileSystemCollector, self).__init__(path_spec_queue)
    self._collect_directory_metadata = True
    self._duplicate_file_check = False
    self._hashlist = {}
    self._resolver_context = resolver_context

  def _CalculateNTFSTimeHash(self, file_entry):
    """Return a hash value calculated from a NTFS file's metadata.

    Args:
      file_entry: the file entry (instance of TSKFileEntry).

    Returns:
      A hash value (string) that can be used to determine if a file's timestamp
    value has changed.
    """
    stat_object = file_entry.GetStat()
    ret_hash = hashlib.md5()

    ret_hash.update(b'atime:{0:d}.{1:d}'.format(
        getattr(stat_object, u'atime', 0),
        getattr(stat_object, u'atime_nano', 0)))

    ret_hash.update(b'crtime:{0:d}.{1:d}'.format(
        getattr(stat_object, u'crtime', 0),
        getattr(stat_object, u'crtime_nano', 0)))

    ret_hash.update(b'mtime:{0:d}.{1:d}'.format(
        getattr(stat_object, u'mtime', 0),
        getattr(stat_object, u'mtime_nano', 0)))

    ret_hash.update(b'ctime:{0:d}.{1:d}'.format(
        getattr(stat_object, u'ctime', 0),
        getattr(stat_object, u'ctime_nano', 0)))

    return ret_hash.hexdigest()

  def _ProcessDataStreams(self, file_entry):
    """Processes the data streams in a file entry.

    Args:
      file_entry: a file entry (instance of dfvfs.FileEntry).
    """
    produced_main_path_spec = False
    for data_stream in file_entry.data_streams:
      # Make a copy so we don't make the changes on a path specification
      # directly. Otherwise already produced path specifications can be
      # altered in the process.
      path_spec = copy.deepcopy(file_entry.path_spec)
      if data_stream.name:
        setattr(path_spec, u'data_stream', data_stream.name)
      self.ProduceItem(path_spec)

      if not data_stream.name:
        produced_main_path_spec = True

    if (not produced_main_path_spec and (
        not file_entry.IsDirectory() or self._collect_directory_metadata)):
      self.ProduceItem(file_entry.path_spec)

  def _ProcessDirectory(self, file_entry):
    """Processes a directory and extract its metadata if necessary.

    Args:
      file_entry: a file entry (instance of dfvfs.FileEntry) that refers
                  to the directory to process.
    """
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
        sub_directories.append(sub_file_entry)

      elif sub_file_entry.IsFile():
        # If we are dealing with a VSS we want to calculate a hash
        # value based on available timestamps and compare that to previously
        # calculated hash values, and only include the file into the queue if
        # the hash does not match.
        if self._duplicate_file_check:
          hash_value = self._CalculateNTFSTimeHash(sub_file_entry)

          inode = getattr(sub_file_entry.path_spec, u'inode', 0)
          if inode in self._hashlist:
            if hash_value in self._hashlist[inode]:
              continue

          self._hashlist.setdefault(inode, []).append(hash_value)

      self._ProcessDataStreams(sub_file_entry)

    for sub_file_entry in sub_directories:
      if self._abort:
        return

      try:
        self._ProcessDirectory(sub_file_entry)
      except (
          dfvfs_errors.AccessError, dfvfs_errors.BackEndError,
          dfvfs_errors.PathSpecError) as exception:
        logging.warning(u'{0:s}'.format(exception))

  def Collect(self, file_system, path_spec, find_specs=None):
    """Collects files from the file system.

    Args:
      file_system: the file system (instance of dfvfs.FileSystem).
      path_spec: the path specification (instance of dfvfs.PathSpec).
      find_specs: optional list of find specifications (instances of
                  dfvfs.FindSpec).
    """
    if find_specs:
      searcher = file_system_searcher.FileSystemSearcher(file_system, path_spec)

      for path_spec in searcher.Find(find_specs=find_specs):
        if self._abort:
          return

        self.ProduceItem(path_spec)

    else:
      file_entry = file_system.GetFileEntryByPathSpec(path_spec)

      self._ProcessDirectory(file_entry)

  def SetCollectDirectoryMetadata(self, collect_directory_metadata):
    """Sets the collect directory metadata flag.

    Args:
      collect_directory_metadata: boolean value to indicate to collect
                                  directory metadata.
    """
    self._collect_directory_metadata = collect_directory_metadata
