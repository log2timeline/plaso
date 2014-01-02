#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
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
"""The SleuthKit collector object implementation."""

import hashlib
import logging
import re

from plaso.collector import interface
from plaso.collector import tsk_helper
from plaso.lib import collector_filter
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import storage_helper
from plaso.lib import utils
from plaso.parsers import filestat
from plaso.pvfs import pfile_entry
from plaso.pvfs import pvfs
from plaso.pvfs import utils as pvfs_utils
from plaso.pvfs import vss

import pytsk3


def CalculateNTFSTimeHash(file_entry):
  """Return a hash value calculated from a NTFS file's metadata.

  Args:
    file_entry: The file entry (instance of TSKFileEntry).

  Returns:
    A hash value (string) that can be used to determine if a file's timestamp
    value has changed.
  """
  stat_object = file_entry.Stat()

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


class TSKCollector(interface.PfileCollector):
  """Class that implements a pfile-based collector object that uses pytsk3."""

  SECTOR_SIZE = 512

  def __init__(
      self, process_queue, output_queue, source_path, sector_offset=0,
      byte_offset=0, parse_vss=False, vss_stores=None, fscache=None):
    """Initializes the collector object.

    Args:
      directory: Path to the directory that contains the files to be collected.
      proces_queue: The files processing queue (instance of
                    queue.QueueInterface).
      output_queue: The event output queue (instance of queue.QueueInterface).
                    This queue is used as a buffer to the storage layer.
      source_path: Path of the source image file.
      sector_offset: An offset into the image file if this is a disk image (in
                     sector size, not byte size).
      byte_offset: A bytes offset into the image file if this is a disk image.
                   image. The default is 0.
      parse_vss: Boolean determining if we should collect from VSS as well
                 (only applicaple in Windows with Volume Shadow Snapshot).
      vss_stores: If defined a range of VSS stores to include in vss parsing.
      fscache: A FilesystemCache object.
    """
    super(TSKCollector, self).__init__(process_queue, output_queue, source_path)
    self._fscache = fscache or pvfs.FilesystemCache()
    self._hashlist = None
    self._sector_offset = sector_offset
    self._byte_offset = byte_offset
    self._vss = parse_vss
    self._vss_stores = vss_stores

  def _CopyPathToPathSpec(
      self, inode_number, path, image_path, image_offset, store_number=None):
    """Copies the path to a path specification equivalent."""
    path_spec = event.EventPathSpec()

    if store_number is not None:
      path_spec.type = 'VSS'
      path_spec.vss_store_number = store_number
    else:
      path_spec.type = 'TSK'

    path_spec.container_path = image_path
    path_spec.image_offset = image_offset
    path_spec.image_inode = inode_number
    path_spec.file_path = utils.GetUnicodeString(path)
    return path_spec

  def _GetImageByteOffset(self):
    """Retrieves the image offset in bytes."""
    return self._byte_offset or self._sector_offset * self.SECTOR_SIZE

  def _GetVssStores(self):
    """Returns a list of VSS stores that need to be processed."""
    image_offset = self._GetImageByteOffset()

    list_of_vss_stores = []
    if not self._vss:
      return list_of_vss_stores

    logging.debug(u'Searching for VSS')
    vss_numbers = vss.GetVssStoreCount(self._source_path, image_offset)
    if self._vss_stores:
      for nr in self._vss_stores:
        if nr > 0 and nr <= vss_numbers:
          list_of_vss_stores.append(nr)
    else:
      list_of_vss_stores = range(0, vss_numbers)

    return list_of_vss_stores

  def _ProcessDirectory(self, file_system_container, file_entry, retry=False):
    """Processes a directory and extract its metadata if necessary.

       Recursive traversal through a directory that injects every file
       that is detected into the processing queue.

    Args:
      file_system_container: The file system object (instance of
                             FilesystemContainer).
      file_entry: The file entry (instance of TSKFileEntry).
      retry: Optional value indicating this is a second attempt at processing
             the directory.
    """
    # TODO: Ignoring retry for now it will be removed in a follow up CL.
    _ = retry

    # Need to do a breadth-first search otherwise we'll hit the Python
    # maximum recursion depth.
    sub_directories = []

    for sub_file_entry in file_entry.GetSubFileEntries():
      # Work-around the limitation in TSKFileEntry that it needs to be open
      # to return stat information. This will be fixed by PyVFS.
      try:
        _  = sub_file_entry.Open()
      except AttributeError as e:
        logging.error(
            u'Unable to read file: {0:s} from image with error: {1:s}'.format(
                sub_file_entry.pathspec.file_path, e))
        continue

      # TODO: Add a test that tests the reason for this. Why is this?
      # If an inode/file gets reallocated yet is still listed inside
      # a directory node there may be issues (reparsing a file, ending
      # up in an endless loop, etc.).
      if not sub_file_entry.IsAllocated():
        # TODO: Perhaps add a direct parsing of timestamps here to include
        # in the timeline.
        continue

      # Ignore the virtual $OrphanFiles directory.
      if sub_file_entry.directory_entry_name == '$OrphanFiles':
        continue

      # We only care about regular files and directories.
      if sub_file_entry.IsDirectory():
        if self.collect_directory_metadata:
          # TODO: solve this differently by putting the path specification
          # on the queue and have the filestat parser just extract the metadata.
          # self._queue.Queue(sub_file_entry.pathspec.ToProtoString())
          stat_object = sub_file_entry.Stat()
          stat_object.full_path = sub_file_entry.pathspec.file_path
          stat_object.display_path = u'{0:s}:{1:s}'.format(
              self._source_path, sub_file_entry.pathspec.file_path)

          try:
            _ = stat_object.display_path.decode('utf-8')
          except UnicodeDecodeError:
            logging.warning(
                u'UnicodeDecodeError: stat_object.display_path: {0:s}'.format(
                    stat_object.display_path))
            stat_object.display_path = utils.GetUnicodeString(
                stat_object.display_path)

          storage_helper.SendContainerToStorage(
              filestat.GetEventContainerFromStat(stat_object), stat_object,
              self._storage_queue)

        sub_directories.append(sub_file_entry)

      elif sub_file_entry.IsFile():
        # If we are dealing with a VSS we want to calculate a hash
        # value based on available timestamps and compare that to previously
        # calculated hash values, and only include the file into the queue if
        # the hash does not match.
        if self._vss:
          hash_value = CalculateNTFSTimeHash(sub_file_entry)

          if sub_file_entry.pathspec.image_inode in self._hashlist:
            if hash_value in self._hashlist[
                sub_file_entry.pathspec.image_inode]:
              continue

          self._hashlist.setdefault(
              sub_file_entry.pathspec.image_inode, []).append(hash_value)

        self._queue.Queue(sub_file_entry.pathspec.ToProtoString())

    for sub_file_entry in sub_directories:
      self._ProcessDirectory(file_system_container, sub_file_entry)

  def _ProcessImage(self):
    """Processes the image."""
    image_offset = self._GetImageByteOffset()
    logging.debug(
        u'Collecting from image file: {0:s}'.format(self._source_path))

    # Check if we will in the future collect from VSS.
    if self._vss:
      self._hashlist = {}

    # Read the root dir, and move from there.
    try:
      file_system_container = self._fscache.Open(
          self._source_path, byte_offset=image_offset)
      # TODO: why was os.path.sep passed here instead of / but not for the VSS?
      root_path_spec = self._CopyPathToPathSpec(
          file_system_container.fs.info.root_inum, u'/',
          file_system_container.path, file_system_container.offset)
      # TODO: do we need to set root here?
      root_file_entry = pfile_entry.TSKFileEntry(
          root_path_spec, root=None, fscache=self._fscache)

      # Work-around the limitation in TSKFileEntry that it needs to be open
      # to return stat information. This will be fixed by PyVFS.
      try:
        _  = root_file_entry.Open()
      except AttributeError as e:
        logging.error((
            u'Unable to read root file entry from image with error: '
            u'{0:s}').format(e))

      self._ProcessDirectory(file_system_container, root_file_entry)

    except errors.UnableToOpenFilesystem as e:
      logging.error(u'Unable to read image with error {0:s}.'.format(e))
      return

    vss_numbers = 0
    if self._vss:
      logging.info(u'Collecting from VSS.')
      vss_numbers = vss.GetVssStoreCount(self._source_path, image_offset)

    for store_number in self._GetVssStores():
      logging.info(u'Collecting from VSS store number: {0:d}/{1:d}'.format(
          store_number + 1, vss_numbers))
      self._ProcessVss(store_number)

    logging.debug(u'Simple Image Collector - Done.')

  def _ProcessImageWithFilter(self):
    """Processes the image with the collection filter."""
    image_offset = self._GetImageByteOffset()
    preprocessor_collector = TSKFilePreprocessCollector(
        self._pre_obj, self._source_path, image_offset)

    try:
      filter_object = collector_filter.CollectionFilter(
          preprocessor_collector, self._filter_file_path)

      for pathspec_string in filter_object.GetPathSpecs():
        self._queue.Queue(pathspec_string)

      if self._vss:
        logging.debug(u'Searching for VSS')
        vss_numbers = vss.GetVssStoreCount(self._source_path, image_offset)
        for store_number in self._GetVssStores():
          logging.info(u'Collecting from VSS store number: {0:s}/{1:s}'.format(
              store_number + 1, vss_numbers))
          vss_collector = VSSFilePreprocessCollector(
              self._pre_obj, self._source_path, store_number,
              byte_offset=image_offset)

          for pathspec_string in collector_filter.CollectionFilter(
              vss_collector, self._filter_file_path).GetPathSpecs():
            self._queue.Queue(pathspec_string)
    finally:
      logging.debug(u'Targeted Image Collector - Done.')

  def _ProcessVss(self, store_number):
    """Processes a Volume Shadow Snapshot (VSS) in the image.

    Args:
      store_number: The VSS store index number.
    """
    logging.debug(u'Collecting from VSS store {0:s}'.format(store_number))
    image_offset = self._GetImageByteOffset()

    try:
      file_system_container = self._fscache.Open(
          self._source_path, byte_offset=image_offset,
          store_number=store_number)
      root_path_spec = self._CopyPathToPathSpec(
          file_system_container.fs.info.root_inum, u'/',
          file_system_container.path, file_system_container.offset,
          store_number=store_number)
      # TODO: do we need to set root here?
      root_file_entry = pfile_entry.TSKFileEntry(
          root_path_spec, root=None, fscache=self._fscache)

      # Work-around the limitation in TSKFileEntry that it needs to be open
      # to return stat information. This will be fixed by PyVFS.
      try:
        _  = root_file_entry.Open()
      except AttributeError as e:
        logging.error((
            u'Unable to read root file entry from image with error: '
            u'{0:s}').format(e))

      self._ProcessDirectory(file_system_container, root_file_entry)

    except errors.UnableToOpenFilesystem as e:
      logging.error(u'Unable to read filesystem with error: {0:s}.'.format(e))

    logging.debug(
        u'Collection from VSS store: {0:d} COMPLETED.'.format(store_number))

  def Collect(self):
    """Start the collection."""
    if self._filter_file_path:
      self._ProcessImageWithFilter()
    else:
      self._ProcessImage()


class TSKFilePreprocessCollector(interface.PreprocessCollector):
  """A wrapper around collecting files from TSK images."""

  _BYTES_PER_SECTOR = 512

  def __init__(self, pre_obj, source_path, byte_offset=0):
    """Initializes the preprocess collector object.

    Args:
      pre_obj: The pre-processing object.
      source_path: Path of the source image file.
      byte_offset: Optional byte offset into the image file if this is a disk
                   image. The default is 0.
    """
    super(TSKFilePreprocessCollector, self).__init__(pre_obj)
    self._source_path = source_path
    self._image_offset = byte_offset
    self._fscache = pvfs.FilesystemCache()
    self._fs_obj = self._fscache.Open(source_path, byte_offset=byte_offset)

  def GetPaths(self, path_list):
    """Find the path if it exists.

    Args:
      path_list: A list of either regular expressions or expanded
                 paths (strings).

    Returns:
      A list of paths.
    """
    return tsk_helper.GetTSKPaths(path_list, self._fs_obj)

  def GetFilePaths(self, path, file_name):
    """Return a list of files given a path and a pattern."""
    ret = []
    file_re = re.compile(r'^{0:s}$'.format(file_name), re.I | re.S)
    try:
      directory = self._fs_obj.fs.open_dir(path)
    except IOError as e:
      raise errors.PreProcessFail(
          u'Unable to open directory: {0:s} with error: {1:s}'.format(path, e))

    for tsk_file in directory:
      try:
        f_type = tsk_file.info.meta.type
        name = tsk_file.info.name.name
      except AttributeError:
        continue
      if f_type == pytsk3.TSK_FS_META_TYPE_REG:
        m = file_re.match(name)
        if m:
          ret.append(u'{0:s}/{1:s}'.format(path, name))

    return ret

  def OpenFileEntry(self, path):
    """Opens a file entry object from the path."""
    return pvfs_utils.OpenTskFileEntry(
        path, self._source_path,
        int(self._image_offset / self._BYTES_PER_SECTOR), self._fscache)

  def ReadingFromImage(self):
    """Indicates if the collector is reading from an image file."""
    return True


class VSSFilePreprocessCollector(TSKFilePreprocessCollector):
  """A wrapper around collecting files from a VSS store from an image file."""

  def __init__(self, pre_obj, source_path, store_number, byte_offset=0):
    """Initializes the preprocess collector object.

    Args:
      pre_obj: The pre-processing object.
      source_path: Path of the source image file.
      store_number: The VSS store index number.
      byte_offset: Optional byte offset into the image file if this is a disk
                   image. The default is 0.
    """
    super(VSSFilePreprocessCollector, self).__init__(
        pre_obj, source_path, byte_offset=byte_offset)
    self._store_number = store_number
    self._fscache = pvfs.FilesystemCache()
    self._fs_obj = self._fscache.Open(
        source_path, byte_offset=byte_offset, store_number=store_number)

  def OpenFileEntry(self, path):
    """Opens a file entry object from the path."""
    return pvfs_utils.OpenVssFileEntry(
        path, self._source_path, self._store_number,
        int(self._source_path / self._BYTES_PER_SECTOR), self._fscache)
