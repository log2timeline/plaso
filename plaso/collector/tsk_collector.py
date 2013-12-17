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
import os

import pytsk3

from plaso.collector import interface
from plaso.collector import tsk_helper
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import storage_helper
from plaso.lib import utils
from plaso.parsers import filestat
from plaso.pvfs import pvfs
from plaso.pvfs import vss


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


class TSKCollector(interface.Collector):
  """Class that implements a collector object that uses pytsk3."""

  SECTOR_SIZE = 512

  def __init__(
      self, process_queue, output_queue, image, sector_offset=0, byte_offset=0,
      parse_vss=False, vss_stores=None, fscache=None, add_dir_stat=True):
    """Initializes the collector object.

    Args:
      directory: Path to the directory that contains the files to be collected.
      proces_queue: The files processing queue (instance of
                    queue.QueueInterface).
      output_queue: The event output queue (instance of queue.QueueInterface).
                    This queue is used as a buffer to the storage layer.
      image: A full path to the image file.
      sector_offset: An offset into the image file if this is a disk image (in
                     sector size, not byte size).
      byte_offset: A bytes offset into the image file if this is a disk image.
                   image. The default is 0.
      parse_vss: Boolean determining if we should collect from VSS as well
                 (only applicaple in Windows with Volume Shadow Snapshot).
      vss_stores: If defined a range of VSS stores to include in vss parsing.
      fscache: A FilesystemCache object.
      add_dir_stat: Optional boolean value to indicate whether or not we want to
                    include directory stat information into the storage queue.
                    The default is true.
    """
    super(TSKCollector, self).__init__(
        process_queue, output_queue, add_dir_stat=add_dir_stat)
    self._image = image
    self._offset = sector_offset
    self._offset_bytes = byte_offset
    self._vss = parse_vss
    self._vss_stores = vss_stores
    self._fscache = fscache or pvfs.FilesystemCache()

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
      if self._dir_stat:
        directory_stat = tsk_helper.GetTskDirectoryStat(directory)
        directory_stat.full_path = path
        directory_stat.display_path = '{}:{}'.format(self._image, path)
        try:
          directory_stat.display_path.decode('utf-8')
        except UnicodeDecodeError:
          directory_stat.display_path = utils.GetUnicodeString(
              directory_stat.display_path)
        storage_helper.SendContainerToStorage(
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
