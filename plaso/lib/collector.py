#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""This is a file collector for Plaso, finding files needed to be parsed.

The classes here are used to fill a queue of PathSpec protobufs that need
to be further processed by the tool.
"""
import abc
import hashlib
import logging
import os

import pytsk3

from plaso.lib import collector_filter
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import pfile
from plaso.lib import preprocess
from plaso.lib import utils
from plaso.lib import vss
from plaso.parsers import filestat


def GetTskDirectoryStat(directory_object):
  """Return a stat object for a TSK directory object.

  Args:
    directory_object: A pyts3k.Directory object.

  Returns:
    A pfile.Stats object for the directory.
  """
  stat = pfile.Stats()

  info = getattr(directory_object, 'info', None)
  if not info:
    return stat

  try:
    meta = info.fs_file.meta
  except AttributeError:
    return stat

  if not meta:
    return stat

  fs_type = ''
  stat.mode = getattr(meta, 'mode', None)
  stat.ino = getattr(meta, 'addr', None)
  stat.nlink = getattr(meta, 'nlink', None)
  stat.uid = getattr(meta, 'uid', None)
  stat.gid = getattr(meta, 'gid', None)
  stat.size = getattr(meta, 'size', None)
  stat.atime = getattr(meta, 'atime', None)
  stat.atime_nano = getattr(meta, 'atime_nano', None)
  stat.crtime = getattr(meta, 'crtime', None)
  stat.crtime_nano = getattr(meta, 'crtime_nano', None)
  stat.mtime = getattr(meta, 'mtime', None)
  stat.mtime_nano = getattr(meta, 'mtime_nano', None)
  stat.ctime = getattr(meta, 'ctime', None)
  stat.ctime_nano = getattr(meta, 'ctime_nano', None)
  stat.dtime = getattr(meta, 'dtime', None)
  stat.dtime_nano = getattr(meta, 'dtime_nano', None)
  stat.bkup_time = getattr(meta, 'bktime', None)
  stat.bkup_time_nano = getattr(meta, 'bktime_nano', None)
  fs_type = str(info.fs_info.ftype)

  if fs_type.startswith('TSK_FS_TYPE'):
    stat.fs_type = fs_type[12:]
  else:
    stat.fs_type = fs_type

  return stat


def GetOsDirectoryStat(directory_path):
  """Return a stat object for an OS directory object.

  Args:
    directory_path: Path to the directory.

  Returns:
    A stat object for the directory.
  """
  ret = pfile.Stats()
  stat = os.stat(directory_path)

  ret.full_path = directory_path
  ret.display_path = directory_path
  ret.mode = stat.st_mode
  ret.ino = stat.st_ino
  ret.dev = stat.st_dev
  ret.nlink = stat.st_nlink
  ret.uid = stat.st_uid
  ret.gid = stat.st_gid
  ret.size = stat.st_size
  if stat.st_atime > 0:
    ret.atime = stat.st_atime
  if stat.st_mtime > 0:
    ret.mtime = stat.st_mtime
  if stat.st_ctime > 0:
    ret.ctime = stat.st_ctime
  ret.fs_type = 'Unknown'
  ret.allocated = True

  return ret


def SendContainerToStorage(container, stat, storage_queue):
  """Read events from a container and send them to storage.

  Args:
    container: An event.EventContainer object that contains
    all the extracted timestamp events from a directory.
    stat: A pfile.Stats object that contains stat information.
    storage_queue: The storage queue to send extracted events to.
  """
  for event_object in container:
    event_object.filename = getattr(stat, 'full_path', '<unknown>')
    event_object.display_name = getattr(
        stat, 'display_path', event_object.filename)
    event_object.parser = u'PfileStatParser'
    event_object.inode = utils.GetInodeValue(stat.ino)
    storage_queue.AddEvent(event_object.ToProtoString())


def CalculateNTFSTimeHash(meta):
  """Return a hash value calculated from a NTFS file's metadata.

  Args:
    meta: A file system metadata (TSK_FS_META) object.

  Returns:
    A hash value (string) that can be used to determine if a file's timestamp
    value has changed.
  """
  ret_hash = hashlib.md5()

  ret_hash.update('atime:{0}.{1}'.format(
      getattr(meta, 'atime', 0),
      getattr(meta, 'atime_nano', 0)))

  ret_hash.update('crtime:{0}.{1}'.format(
      getattr(meta, 'crtime', 0),
      getattr(meta, 'crtime_nano', 0)))

  ret_hash.update('mtime:{0}.{1}'.format(
      getattr(meta, 'mtime', 0),
      getattr(meta, 'mtime_nano', 0)))

  ret_hash.update('ctime:{0}.{1}'.format(
      getattr(meta, 'ctime', 0),
      getattr(meta, 'ctime_nano', 0)))

  return ret_hash.hexdigest()


class Collector(object):
  """An interface for file collection in Plaso."""

  def __init__(self, proc_queue, stor_queue):
    """Initialize the Collector.

    The collector takes care of discovering all the files that need to be
    processed. Once a file is discovered it is described using a EventPathSpec
    object and inserted into a processing queue.

    Args:
      proc_queue: A Plaso queue object used as a processing queue of files.
      stor_queue: A Plaso queue object used as a buffer to the storage layer.
    """
    self._queue = proc_queue
    self._storage_queue = stor_queue

  def Run(self):
    """Run the collector and then close the queue."""
    self.Collect()
    self.Close()

  @abc.abstractmethod
  def Collect(self):
    """Discover all files that need processing and include in the queue."""
    pass

  def Close(self):
    """Close the queue."""
    self._queue.Close()

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self.Close()

  def __enter__(self):
    """Make usable with "with" statement."""
    return self


class SimpleFileCollector(Collector):
  """This is a simple collector that collects from a directory."""

  def __init__(self, proc_queue, stor_queue, directory):
    """Initialize the file collector.

    Args:
      proc_queue: A Plaso queue object used as a processing queue of files.
      stor_queue: A Plaso queue object used as a buffer to the storage layer.
      directory: Path to the directory that contains files to be collected.
    """
    super(SimpleFileCollector, self).__init__(proc_queue, stor_queue)
    self._dir = directory

  def Collect(self):
    """Recursive traversal of a directory."""
    if os.path.isfile(self._dir):
      self.ProcessFile(self._dir)
      return

    if not os.path.isdir(self._dir):
      logging.error((
          u'Unable to collect, [%s] is neither a file nor a '
          'directory.'), self._dir)
      return

    for root, _, files in os.walk(self._dir):
      self.ProcessDir(root)
      for filename in files:
        try:
          path = os.path.join(root, filename)
          if os.path.islink(path):
            continue
          if os.path.isfile(path):
            self.ProcessFile(path)
        except IOError as e:
          logging.warning('Unable to further process %s:%s', filename, e)

  def ProcessDir(self, path):
    """Process a directory and extract timestamps from it."""
    # Get a stat object and send timestamps for the directory to the storage.
    directory_stat = GetOsDirectoryStat(path)
    SendContainerToStorage(
        filestat.GetEventContainerFromStat(directory_stat),
        directory_stat, self._storage_queue)

  def ProcessFile(self, filename):
    """Finds all files available inside a file and inserts into queue."""
    transfer_proto = event.EventPathSpec()
    transfer_proto.type = 'OS'
    transfer_proto.file_path = utils.GetUnicodeString(filename)
    self._queue.Queue(transfer_proto.ToProtoString())


class SimpleImageCollector(Collector):
  """This is a simple collector that collects from an image file."""

  SECTOR_SIZE = 512

  def __init__(self, proc_queue, stor_queue, image, offset=0, offset_bytes=0,
               parse_vss=False, vss_stores=None, fscache=None):
    """Initialize the image collector.

    Args:
      proc_queue: A Plaso queue object used as a processing queue of files.
      stor_queue: A Plaso queue object used as a buffer to the storage layer.
      image: A full path to the image file.
      offset: An offset into the image file if this is a disk image (in sector
      size, not byte size).
      offset_bytes: A bytes offset into the image file if this is a disk image.
      parse_vss: Boolean determining if we should collect from VSS as well
      (only applicaple in Windows with Volume Shadow Snapshot).
      vss_stores: If defined a range of VSS stores to include in vss parsing.
      fscache: A FilesystemCache object.
    """
    super(SimpleImageCollector, self).__init__(proc_queue, stor_queue)
    self._image = image
    self._offset = offset
    self._offset_bytes = offset_bytes
    self._vss = parse_vss
    self._vss_stores = vss_stores
    self._fscache = fscache or pfile.FilesystemCache()

  def GetVssStores(self, offset):
    """Return a list of VSS stores that needs to be checked."""
    stores = []
    if not self._vss:
      return stores

    logging.debug(u'Searching for VSS')
    vss_numbers = vss.GetVssStoreCount(self._image, offset)
    if self._vss_stores:
      for nr in self._vss_stores:
        if nr > 0 and nr <= vss_numbers:
          stores.append(nr)
    else:
      stores = range(0, vss_numbers)

    return stores

  def Collect(self):
    """Start the collection."""
    offset = self._offset_bytes or self._offset * self.SECTOR_SIZE
    logging.debug(u'Collecting from an image file [%s]', self._image)

    # Check if we will in the future collect from VSS.
    if self._vss:
      self._hashlist = {}

    try:
      fs = self._fscache.Open(self._image, offset)
      # Read the root dir, and move from there.
      self.ParseImageDir(fs, fs.fs.info.root_inum, os.path.sep)
    except errors.UnableToOpenFilesystem as e:
      logging.error(u'Unable to read image [no collection] - %s.', e)
      return

    vss_numbers = 0
    if self._vss:
      logging.info(u'Collecting from VSS.')
      vss_numbers = vss.GetVssStoreCount(self._image, offset)

    for store_nr in self.GetVssStores(offset):
      logging.info(
          u'Collecting from VSS store number: %d/%d', store_nr + 1,
          vss_numbers)
      self.CollectFromVss(self._image, store_nr, offset)

    logging.debug(u'Simple Image Collector - Done.')

  def CollectFromVss(self, image_path, store_nr, offset=0):
    """Collect files from a VSS image.

    Args:
      image_path: The path to the TSK image in the filesystem.
      store_nr: The store number for the VSS store.
      offset: An offset into the disk image to where the volume
      lies (sector size, not byte).
    """
    logging.debug(u'Collecting from VSS store %d', store_nr)

    try:
      fs = self._fscache.Open(image_path, offset, store_nr)
      self.ParseImageDir(fs, fs.fs.info.root_inum, '/')
    except errors.UnableToOpenFilesystem as e:
      logging.error(u'Unable to read filesystem: %s.', e)

    logging.debug(u'Collection from VSS store: %d COMPLETED.', store_nr)

  def ParseImageDir(self, fs, cur_inode, path, retry=False):
    """A recursive traversal of a directory inside an image file.

    Recursive traversal through a directory that injects every file
    that is detected into the processing queue.

    Args:
      fs: A CacheFileSystem object that contains information about the
      filesystem being used to collect from.
      cur_inode: The inode number in which the directory begins.
      path: The full path name of the directory (string).
      retry: Boolean indicating this is the second attempt at parsing
      a directory.
    """
    try:
      directory = fs.fs.open_dir(inode=cur_inode)
      # Get a stat object and send timestamps for the directory to the storage.
      directory_stat = GetTskDirectoryStat(directory)
      directory_stat.full_path = path
      directory_stat.display_path = '{}:{}'.format(self._image, path)
      try:
        directory_stat.display_path.decode('utf-8')
      except UnicodeDecodeError:
        directory_stat.display_path = utils.GetUnicodeString(
            directory_stat.display_path)
      SendContainerToStorage(
          filestat.GetEventContainerFromStat(directory_stat),
          directory_stat, self._storage_queue)
    except IOError:
      logging.error(u'IOError while trying to open a directory: %s [%d]',
                    path, cur_inode)
      if not retry:
        logging.info(u'Reopening directory due to an IOError: %s', path)
        self.ParseImageDir(fs, cur_inode, path, True)
      return

    directories = []
    for f in directory:
      try:
        tsk_name = f.info.name
        if not tsk_name:
          continue
        # TODO: Add a test that tests the reason for this. Why is this?
        # If an inode/file gets reallocated yet is still listed inside
        # a directory node there may be issues (reparsing a file, ending
        # up in an endless loop, etc.).
        if tsk_name.flags == pytsk3.TSK_FS_NAME_FLAG_UNALLOC:
          # TODO: Perhaps add a direct parsing of timestamps here to include
          # in the timeline.
          continue
        if not f.info.meta:
          continue
        name_str = tsk_name.name
        inode_addr = f.info.meta.addr
        f_type = f.info.meta.type
      except AttributeError as e:
        logging.error(u'[ParseImage] Problem reading file [%s], error: %s',
                      name_str, e)
        continue

      # List of files we do not want to process further.
      if name_str in ['$OrphanFiles', '.', '..']:
        continue

      # We only care about regular files and directories
      if f_type == pytsk3.TSK_FS_META_TYPE_DIR:
        directories.append((inode_addr, os.path.join(path, name_str)))
      elif f_type == pytsk3.TSK_FS_META_TYPE_REG:
        transfer_proto = event.EventPathSpec()
        if fs.store_nr >= 0:
          transfer_proto.type = 'VSS'
          transfer_proto.vss_store_number = fs.store_nr
        else:
          transfer_proto.type = 'TSK'
        transfer_proto.container_path = fs.path
        transfer_proto.image_offset = fs.offset
        transfer_proto.image_inode = inode_addr
        file_path = os.path.join(path, name_str)
        transfer_proto.file_path = utils.GetUnicodeString(file_path)

        # If we are dealing with a VSS we want to calculate a hash
        # value based on available timestamps and compare that to previously
        # calculated hash values, and only include the file into the queue if
        # the hash does not match.
        if self._vss:
          hash_value = CalculateNTFSTimeHash(f.info.meta)

          if inode_addr in self._hashlist:
            if hash_value in self._hashlist[inode_addr]:
              continue

          self._hashlist.setdefault(inode_addr, []).append(hash_value)
          self._queue.Queue(transfer_proto.ToProtoString())
        else:
          self._queue.Queue(transfer_proto.ToProtoString())

    for inode_addr, path in directories:
      self.ParseImageDir(fs, inode_addr, path)


class TargetedFileSystemCollector(SimpleFileCollector):
  """This is a simple collector that collects using a targeted list."""

  def __init__(
      self, proc_queue, stor_queue, pre_obj, mount_point, file_filter):
    """Initialize the targeted filesystem collector.

    Args:
      proc_queue: A Plaso queue object used as a processing queue of files.
      stor_queue: A Plaso queue object used as a buffer to the storage layer.
      pre_obj: The PlasoPreprocess object.
      mount_point: The path to the mount point or base directory.
      file_filter: The path of the filter file.
    """
    super(TargetedFileSystemCollector, self).__init__(
        proc_queue, stor_queue, mount_point)
    self._collector = preprocess.FileSystemCollector(
        pre_obj, mount_point)
    self._file_filter = file_filter

  def Collect(self):
    """Start the collector."""
    for pathspec_string in collector_filter.CollectionFilter(
        self._collector, self._file_filter).GetPathSpecs():
      self._queue.Queue(pathspec_string)


class TargetedImageCollector(SimpleImageCollector):
  """Targeted collector that works against an image file."""

  def __init__(self, proc_queue, stor_queue, image, file_filter, pre_obj,
               sector_offset=0, byte_offset=0, parse_vss=False,
               vss_stores=None):
    """Initialize the image collector.

    Args:
      proc_queue: A Plaso queue object used as a processing queue of files.
      stor_queue: A Plaso queue object used as a buffer to the storage layer.
      image: The path to the image file.
      file_filter: A file path to a file that contains simple collection
      filters.
      pre_obj: A PlasoPreprocess object.
      sector_offset: A sector offset into the image file if this is a disk
      image.
      byte_offset: A bytes offset into the image file if this is a disk image.
      parse_vss: Boolean determining if we should collect from VSS as well
      (only applicaple in Windows with Volume Shadow Snapshot).
      vss_stores: If defined a range of VSS stores to include in vss parsing.
    """
    super(TargetedImageCollector, self).__init__(
        proc_queue, stor_queue, image, sector_offset, byte_offset, parse_vss,
        vss_stores)
    self._file_filter = file_filter
    self._pre_obj = pre_obj

  def Collect(self):
    """Start the collector."""
    # TODO: Change the parent object so that is uses the sector/byte_offset
    # to minimize confusion.
    offset = self._offset_bytes or self._offset * self.SECTOR_SIZE
    pre_collector = preprocess.TSKFileCollector(
        self._pre_obj, self._image, offset)

    try:
      for pathspec_string in collector_filter.CollectionFilter(
          pre_collector, self._file_filter).GetPathSpecs():
        self._queue.Queue(pathspec_string)

      if self._vss:
        logging.debug(u'Searching for VSS')
        vss_numbers = vss.GetVssStoreCount(self._image, offset)
        for store_nr in self.GetVssStores(offset):
          logging.info(
              u'Collecting from VSS store number: %d/%d', store_nr + 1,
              vss_numbers)
          vss_collector = preprocess.VSSFileCollector(
              self._pre_obj, self._image, store_nr, offset)

          for pathspec_string in collector_filter.CollectionFilter(
              vss_collector, self._file_filter).GetPathSpecs():
            self._queue.Queue(pathspec_string)
    finally:
      logging.debug(u'Targeted Image Collector - Done.')
