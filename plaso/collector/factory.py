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
"""The collector object factory."""
# Note that this is not a real factory class but code that provides
# factory helper functions for the PyVFS migration.

import logging
import os
import re

import pytsk3

from plaso.collector import interface
from plaso.collector import os_collector
from plaso.collector import os_helper
from plaso.collector import tsk_collector
from plaso.collector import tsk_helper
from plaso.lib import collector_filter
from plaso.lib import errors
from plaso.pvfs import pfile
from plaso.pvfs import vss
from plaso.pvfs import utils


class FileSystemPreprocessCollector(interface.PreprocessCollector):
  """A wrapper around collecting files from mount points."""

  def __init__(self, pre_obj, mount_point):
    """Initializes the preprocess collector object.

    Args:
      pre_obj: The pre-processing object.
      mount_point: The path to the mount point or base directory.
    """
    super(FileSystemPreprocessCollector, self).__init__(pre_obj)
    self._mount_point = mount_point

  def GetPaths(self, path_list):
    """Find the path if it exists.

    Args:
      path_list: A list of either regular expressions or expanded
                 paths (strings).

    Returns:
      A list of paths.
    """
    return os_helper.GetOsPaths(path_list, self._mount_point)

  def GetFilePaths(self, path, file_name):
    """Return a list of files given a path and a pattern."""
    ret = []
    file_re = re.compile(r'^%s$' % file_name, re.I | re.S)
    if path == os.path.sep:
      directory = self._mount_point
      path_use = '.'
    else:
      directory = os.path.join(self._mount_point, path)
      path_use = path

    try:
      for entry in os.listdir(directory):
        m = file_re.match(entry)
        if m:
          if os.path.isfile(os.path.join(directory, m.group(0))):
            ret.append(os.path.join(path_use, m.group(0)))
    except OSError as e:
      logging.error(u'Unable to read directory: %s, reason %s', directory, e)
    return ret

  def OpenFile(self, path):
    """Open a file given a path and return a filehandle."""
    return utils.OpenOSFile(os.path.join(self._mount_point, path))

  def ReadingFromImage(self):
    """Indicates if the collector is reading from an image file."""
    return False


class TargetedFileSystemCollector(os_collector.OSCollector):
  """This is a simple collector that collects using a targeted list."""

  def __init__(
      self, proc_queue, stor_queue, pre_obj, mount_point, file_filter,
      add_dir_stat=True):
    """Initialize the targeted filesystem collector.

    Args:
      proc_queue: A Plaso queue object used as a processing queue of files.
      stor_queue: A Plaso queue object used as a buffer to the storage layer.
      pre_obj: The PlasoPreprocess object.
      mount_point: The path to the mount point or base directory.
      file_filter: The path of the filter file.
      add_dir_stat: Optional boolean value to indicate whether or not we want to
                    include directory stat information into the storage queue.
                    The default is true.
    """
    super(TargetedFileSystemCollector, self).__init__(
        proc_queue, stor_queue, mount_point, add_dir_stat=add_dir_stat)
    self._collector = FileSystemPreprocessCollector(
        pre_obj, mount_point)
    self._file_filter = file_filter

  def Collect(self):
    """Start the collector."""
    for pathspec_string in collector_filter.CollectionFilter(
        self._collector, self._file_filter).GetPathSpecs():
      self._queue.Queue(pathspec_string)


class TSKFilePreprocessCollector(interface.PreprocessCollector):
  """A wrapper around collecting files from TSK images."""

  def __init__(self, pre_obj, image_path, byte_offset=0):
    """Initializes the preprocess collector object.

    Args:
      pre_obj: The pre-processing object.
      image_path: The path of the image file.
      byte_offset: Optional byte offset into the image file if this is a disk
                   image. The default is 0.
    """
    super(TSKFilePreprocessCollector, self).__init__(pre_obj)
    self._image_path = image_path
    self._image_offset = byte_offset
    self._fscache = pfile.FilesystemCache()
    self._fs_obj = self._fscache.Open(image_path, byte_offset)

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
    file_re = re.compile(r'^%s$' % file_name, re.I | re.S)
    try:
      directory = self._fs_obj.fs.open_dir(path)
    except IOError as e:
      raise errors.PreProcessFail(
          u'Unable to open directory: %s [%s]' % (path, e))

    for tsk_file in directory:
      try:
        f_type = tsk_file.info.meta.type
        name = tsk_file.info.name.name
      except AttributeError:
        continue
      if f_type == pytsk3.TSK_FS_META_TYPE_REG:
        m = file_re.match(name)
        if m:
          ret.append(u'%s/%s' % (path, name))

    return ret

  def OpenFile(self, path):
    """Open a file given a path and return a filehandle."""
    return utils.OpenTskFile(
        path, self._image_path, int(self._image_offset / 512), self._fscache)

  def ReadingFromImage(self):
    """Indicates if the collector is reading from an image file."""
    return True


class VSSFilePreprocessCollector(TSKFilePreprocessCollector):
  """A wrapper around collecting files from a VSS store from an image file."""

  def __init__(self, pre_obj, image_path, store_nr, byte_offset=0):
    """Initializes the preprocess collector object.

    Args:
      pre_obj: The pre-processing object.
      image_path: The path of the image file.
      store_nr: The VSS store index number.
      byte_offset: Optional byte offset into the image file if this is a disk
                   image. The default is 0.
    """
    super(VSSFilePreprocessCollector, self).__init__(
        pre_obj, image_path, byte_offset=byte_offset)
    self._store_nr = store_nr
    self._fscache = pfile.FilesystemCache()
    self._fs_obj = self._fscache.Open(
        image_path, byte_offset, store_nr)

  def OpenFile(self, path):
    """Open a file given a path and return a filehandle."""
    return utils.OpenVssFile(
        path, self._image_path, self._store_nr, int(self._image_offset / 512),
        self._fscache)


class TargetedImageCollector(tsk_collector.TSKCollector):
  """Targeted collector that works against an image file."""

  def __init__(
     self, proc_queue, stor_queue, image, file_filter, pre_obj, sector_offset=0,
     byte_offset=0, parse_vss=False, vss_stores=None, add_dir_stat=True):
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
      byte_offset: Optional byte offset into the image file if this is a disk
                   image. The default is 0.
      parse_vss: Boolean determining if we should collect from VSS as well
                 (only applicaple in Windows with Volume Shadow Snapshot).
      vss_stores: If defined a range of VSS stores to include in vss parsing.
      add_dir_stat: Optional boolean value to indicate whether or not we want to
                    include directory stat information into the storage queue.
                    The default is true.
    """
    super(TargetedImageCollector, self).__init__(
        proc_queue, stor_queue, image, sector_offset=sector_offset,
        byte_offset=byte_offset, parse_vss=parse_vss, vss_stores=vss_stores,
        add_dir_stat=add_dir_stat)
    self._file_filter = file_filter
    self._pre_obj = pre_obj

  def Collect(self):
    """Start the collector."""
    # TODO: Change the parent object so that is uses the sector/byte_offset
    # to minimize confusion.
    offset = self._offset_bytes or self._offset * self.SECTOR_SIZE
    pre_collector = TSKFilePreprocessCollector(
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
          vss_collector = VSSFilePreprocessCollector(
              self._pre_obj, self._image, store_nr, byte_offset=offset)

          for pathspec_string in collector_filter.CollectionFilter(
              vss_collector, self._file_filter).GetPathSpecs():
            self._queue.Queue(pathspec_string)
    finally:
      logging.debug(u'Targeted Image Collector - Done.')


def GetFileSystemPreprocessCollector(pre_obj, mount_point):
  """Factory function to retrieve an image preprocess collector object.

  Args:
    pre_obj: The pre-processing object.
    mount_point: The path to the mount point or base directory.

  Returns:
    A preprocess collector object (instance of PreprocessCollector).
  """
  return FileSystemPreprocessCollector(pre_obj, mount_point)


def GetImagePreprocessCollector(
    pre_obj, image_path, byte_offset=0, vss_store_number=None):
  """Factory function to retrieve an image preprocess collector object.

  Args:
    pre_obj: The pre-processing object.
    image_path: The path of the image file.
    byte_offset: Optional byte offset into the image file if this is a disk
                 image. The default is 0.
    vss_store_number: Optional VSS store index number. The default is None.

  Returns:
    A preprocess collector object (instance of PreprocessCollector).
  """
  if vss_store_number is not None:
    return VSSFilePreprocessCollector(
        pre_obj, image_path, vss_store_number, byte_offset=byte_offset)
  return TSKFilePreprocessCollector(
      pre_obj, image_path, byte_offset=byte_offset)


def GetFileSystemCollector(
    proc_queue, stor_queue, directory, add_dir_stat=True):
  """Factory function to retrieve a file system collector object.

  Args:
    proc_queue: A Plaso queue object used as a processing queue of files.
    stor_queue: A Plaso queue object used as a buffer to the storage layer.
    directory: Path to the directory that contains files to be collected.
    add_dir_stat: Optional boolean value to indicate whether or not we want to
                  include directory stat information into the storage queue.
                  The default is true.
  """
  return os_collector.OSCollector(
      proc_queue, stor_queue, directory, add_dir_stat=add_dir_stat)


def GetFileSystemCollectorWithFilter(
    proc_queue, stor_queue, pre_obj, mount_point, file_filter,
    add_dir_stat=True):
  """Factory function to retrieve a file system collector object with filter.

  Args:
    proc_queue: A Plaso queue object used as a processing queue of files.
    stor_queue: A Plaso queue object used as a buffer to the storage layer.
    pre_obj: The PlasoPreprocess object.
    mount_point: The path to the mount point or base directory.
    file_filter: The path of the filter file.
    add_dir_stat: Optional boolean value to indicate whether or not we want to
                  include directory stat information into the storage queue.
                  The default is true.

  Returns:
    A collector object (instance of Collector).
  """
  return TargetedFileSystemCollector(
      proc_queue, stor_queue, pre_obj, mount_point, file_filter,
      add_dir_stat=add_dir_stat)


def GetImageCollector(
    proc_queue, stor_queue, image, sector_offset=0, byte_offset=0,
    parse_vss=False, vss_stores=None, fscache=None, add_dir_stat=True):
  """Factory function to retrieve an image collector object.

  Args:
    proc_queue: A Plaso queue object used as a processing queue of files.
    stor_queue: A Plaso queue object used as a buffer to the storage layer.
    image: A full path to the image file.
    sector_offset: A sector offset into the image file if this is a disk
                   image.
    byte_offset: Optional byte offset into the image file if this is a disk
                 image. The default is 0.
    parse_vss: Boolean determining if we should collect from VSS as well
               (only applicaple in Windows with Volume Shadow Snapshot).
    vss_stores: If defined a range of VSS stores to include in vss parsing.
    fscache: A FilesystemCache object.
    add_dir_stat: Optional boolean value to indicate whether or not we want to
                  include directory stat information into the storage queue.
                  The default is true.
  Returns:
    A collector object (instance of Collector).
  """
  return tsk_collector.TSKCollector(
      proc_queue, stor_queue, image, sector_offset=sector_offset,
      byte_offset=byte_offset, parse_vss=parse_vss, vss_stores=vss_stores,
      fscache=fscache, add_dir_stat=add_dir_stat)


def GetImageCollectorWithFilter(
    proc_queue, stor_queue, image, file_filter, pre_obj, sector_offset=0,
    byte_offset=0, parse_vss=False, vss_stores=None, add_dir_stat=True):
  """Factory function to retrieve an image collector object with filter.

  Args:
    proc_queue: A Plaso queue object used as a processing queue of files.
    stor_queue: A Plaso queue object used as a buffer to the storage layer.
    image: The path to the image file.
    file_filter: A file path to a file that contains simple collection
                 filters.
    pre_obj: A PlasoPreprocess object.
    sector_offset: A sector offset into the image file if this is a disk
                   image.
    byte_offset: Optional byte offset into the image file if this is a disk
                 image. The default is 0.
    parse_vss: Boolean determining if we should collect from VSS as well
               (only applicaple in Windows with Volume Shadow Snapshot).
    vss_stores: If defined a range of VSS stores to include in vss parsing.
    add_dir_stat: Optional boolean value to indicate whether or not we want to
                  include directory stat information into the storage queue.
                  The default is true.

  Returns:
    A collector object (instance of Collector).
  """
  return TargetedImageCollector(
      proc_queue, stor_queue, image, file_filter, pre_obj,
      sector_offset=sector_offset, byte_offset=byte_offset, parse_vss=parse_vss,
      vss_stores=vss_stores, add_dir_stat=add_dir_stat)
