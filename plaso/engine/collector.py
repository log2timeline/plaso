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


class Collector(object):
  """Class that implements a source collector object."""

  def __init__(self, duplicate_file_check=False, resolver_context=None):
    """Initializes a source collector object.

    The source collector discovers all the file entries in the source.
    The source can be a single file, directory or a volume within
    a storage media image or device.

    Args:
      duplicate_file_check: optional boolean value to indicate the collector
                            should ignore duplicate files.
      resolver_context: optional resolver context (instance of dfvfs.Context).
    """
    super(Collector, self).__init__()
    self._collect_directory_metadata = True
    self._duplicate_file_check = duplicate_file_check
    self._hashlist = {}
    self._resolver_context = resolver_context

  def _CalculateNTFSTimeHash(self, file_entry):
    """Return a hash value calculated from a NTFS file's metadata.

    Args:
      file_entry: the file entry (instance of FileEntry).

    Returns:
      A hash value (string) that can be used to determine if a file's timestamp
      value has changed.
    """
    stat_object = file_entry.GetStat()
    ret_hash = hashlib.md5()

    atime = getattr(stat_object, u'atime', None)
    if not atime:
      atime = 0
    ret_hash.update(b'atime:{0:d}.{1:d}'.format(
        atime, getattr(stat_object, u'atime_nano', 0)))

    crtime = getattr(stat_object, u'crtime', None)
    if not crtime:
      crtime = 0
    ret_hash.update(b'crtime:{0:d}.{1:d}'.format(
        crtime, getattr(stat_object, u'crtime_nano', 0)))

    mtime = getattr(stat_object, u'mtime', None)
    if not mtime:
      mtime = 0
    ret_hash.update(b'mtime:{0:d}.{1:d}'.format(
        mtime, getattr(stat_object, u'mtime_nano', 0)))

    ctime = getattr(stat_object, u'ctime', None)
    if not ctime:
      ctime = 0
    ret_hash.update(b'ctime:{0:d}.{1:d}'.format(
        ctime, getattr(stat_object, u'ctime_nano', 0)))

    return ret_hash.hexdigest()

  def _CollectPathSpecsFromDirectory(self, file_entry):
    """Collects path specification from a directory.

    Args:
      file_entry: a file entry (instance of dfvfs.FileEntry) that refers
                  to the directory to process.

    Yields:
      Path specifications (instances of dfvfs.PathSpec) of file entries
      found in the directory.
    """
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

      for path_spec in self._CollectPathSpecsFromFile(sub_file_entry):
        yield path_spec

    for sub_file_entry in sub_directories:
      try:
        for path_spec in self._CollectPathSpecsFromDirectory(sub_file_entry):
          yield path_spec

      except (
          dfvfs_errors.AccessError, dfvfs_errors.BackEndError,
          dfvfs_errors.PathSpecError) as exception:
        logging.warning(u'{0:s}'.format(exception))

  def _CollectPathSpecsFromFile(self, file_entry):
    """Collects path specification from a file.

    Args:
      file_entry: a file entry (instance of dfvfs.FileEntry).

    Yields:
      Path specifications (instances of dfvfs.PathSpec) of file entries
      found in the file entry.
    """
    produced_main_path_spec = False
    for data_stream in file_entry.data_streams:
      # Make a copy so we don't make the changes on a path specification
      # directly. Otherwise already produced path specifications can be
      # altered in the process.
      path_spec = copy.deepcopy(file_entry.path_spec)
      if data_stream.name:
        setattr(path_spec, u'data_stream', data_stream.name)
      yield path_spec

      if not data_stream.name:
        produced_main_path_spec = True

    if (not produced_main_path_spec and (
        not file_entry.IsDirectory() or self._collect_directory_metadata)):
      yield file_entry.path_spec

  def _CollectPathSpecsFromFileSystem(self, path_spec, find_specs=None):
    """Collects path specification from a file system within a specific source.

    Args:
      path_spec: a path specification (instance of dfvfs.PathSpec)
                 of the root of the file system.
      find_specs: optional list of find specifications (instances of
                  dfvfs.FindSpec).

    Yields:
      Path specifications (instances of dfvfs.PathSpec) of file entries
      found in the file system.
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
      if find_specs:
        searcher = file_system_searcher.FileSystemSearcher(
            file_system, path_spec)
        for path_spec in searcher.Find(find_specs=find_specs):
          yield path_spec

      else:
        file_entry = file_system.GetFileEntryByPathSpec(path_spec)
        if file_entry:
          for path_spec in self._CollectPathSpecsFromDirectory(file_entry):
            yield path_spec

    except (
        dfvfs_errors.AccessError, dfvfs_errors.BackEndError,
        dfvfs_errors.PathSpecError) as exception:
      logging.warning(u'{0:s}'.format(exception))

    finally:
      file_system.Close()

  def CollectPathSpecs(self, path_spec, find_specs=None):
    """Collects path specification from a specific source.

    Args:
      path_spec: the path specification (instance of dfvfs.path.PathSpec)
                 to process.
      find_specs: optional list of find specifications (instances of
                  dfvfs.FindSpec).

    Yields:
      Path specifications (instances of dfvfs.PathSpec) of file entries
      found in the source.
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
      yield path_spec

    else:
      for path_spec in self._CollectPathSpecsFromFileSystem(
          path_spec, find_specs=find_specs):
        yield path_spec

  def SetCollectDirectoryMetadata(self, collect_directory_metadata):
    """Sets the collect directory metadata flag.

    Args:
      collect_directory_metadata: boolean value to indicate to collect
                                  directory metadata.
    """
    self._collect_directory_metadata = collect_directory_metadata


class CollectorQueueProducer(plaso_queue.ItemQueueProducer):
  """Class that implements a collector queue producer object."""

  def __init__(self, path_spec_queue, resolver_context=None):
    """Initializes the collector queue producer object.

    The collector queue producer discovers all the files that need to
    be processed by the workers. Once a file is discovered it is added
    to the process queue as a path specification (instance of dfvfs.PathSpec).

    Args:
      path_spec_queue: the path specification queue (instance of Queue).
                       This queue contains path specifications (instances
                       of dfvfs.PathSpec) of the file entries that need
                       to be processed.
      resolver_context: optional resolver context (instance of dfvfs.Context).
    """
    super(CollectorQueueProducer, self).__init__(path_spec_queue)
    self._collector = Collector(resolver_context=resolver_context)
    self._filter_find_specs = None

    # Attributes that contain the current status of the collector.
    self._status = definitions.PROCESSING_STATUS_INITIALIZED

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
      for path_spec in self._collector.CollectPathSpecs(
          source_path_spec, find_specs=self._filter_find_specs):
        self.ProduceItem(path_spec)

    if self._abort:
      self._status = definitions.PROCESSING_STATUS_ABORTED
    else:
      self._status = definitions.PROCESSING_STATUS_COMPLETED

  def GetStatus(self):
    """Returns a dictionary containing the status."""
    return {
        u'processing_status': self._status,
        u'produced_number_of_path_specs': self._number_of_produced_items,
        u'path_spec_queue_port': getattr(self._queue, u'port', None),
        u'type': definitions.PROCESS_TYPE_COLLECTOR}

  def SetCollectDirectoryMetadata(self, collect_directory_metadata):
    """Sets the collect directory metadata flag.

    Args:
      collect_directory_metadata: boolean value to indicate to collect
                                  directory metadata.
    """
    self._collector.SetCollectDirectoryMetadata(collect_directory_metadata)

  def SetFilter(self, filter_find_specs):
    """Sets the collection filter find specifications.

    Args:
      filter_find_specs: list of filter find specifications (instances of
                         dfvfs.FindSpec).
    """
    self._filter_find_specs = filter_find_specs
