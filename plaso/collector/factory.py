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

from plaso.collector import os_collector
from plaso.collector import tsk_collector
from plaso.lib import collector_filter
from plaso.pvfs import vss


class TargetedImageCollector(tsk_collector.TSKCollector):
  """Targeted collector that works against an image file."""

  def __init__(
     self, proc_queue, stor_queue, image, file_filter, pre_obj, sector_offset=0,
     byte_offset=0, parse_vss=False, vss_stores=None):
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
    """
    super(TargetedImageCollector, self).__init__(
        proc_queue, stor_queue, image, sector_offset=sector_offset,
        byte_offset=byte_offset, parse_vss=parse_vss, vss_stores=vss_stores)
    self._file_filter = file_filter
    self._pre_obj = pre_obj

  def Collect(self):
    """Start the collector."""
    # TODO: Change the parent object so that is uses the sector/byte_offset
    # to minimize confusion.
    offset = self._offset_bytes or self._offset * self.SECTOR_SIZE
    pre_collector = tsk_collector.TSKFilePreprocessCollector(
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
          vss_collector = tsk_collector.VSSFilePreprocessCollector(
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
  return os_collector.FileSystemPreprocessCollector(pre_obj, mount_point)


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
    return tsk_collector.VSSFilePreprocessCollector(
        pre_obj, image_path, vss_store_number, byte_offset=byte_offset)
  return tsk_collector.TSKFilePreprocessCollector(
      pre_obj, image_path, byte_offset=byte_offset)


def GetFileSystemCollector(proc_queue, stor_queue, directory):
  """Factory function to retrieve a file system collector object.

  Args:
    proc_queue: A Plaso queue object used as a processing queue of files.
    stor_queue: A Plaso queue object used as a buffer to the storage layer.
    directory: Path to the directory that contains files to be collected.
  """
  return os_collector.OSCollector(proc_queue, stor_queue, directory)


def GetImageCollector(
    proc_queue, stor_queue, image, sector_offset=0, byte_offset=0,
    parse_vss=False, vss_stores=None, fscache=None):
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
  Returns:
    A collector object (instance of Collector).
  """
  return tsk_collector.TSKCollector(
      proc_queue, stor_queue, image, sector_offset=sector_offset,
      byte_offset=byte_offset, parse_vss=parse_vss, vss_stores=vss_stores,
      fscache=fscache)


def GetImageCollectorWithFilter(
    proc_queue, stor_queue, image, file_filter, pre_obj, sector_offset=0,
    byte_offset=0, parse_vss=False, vss_stores=None):
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

  Returns:
    A collector object (instance of Collector).
  """
  return TargetedImageCollector(
      proc_queue, stor_queue, image, file_filter, pre_obj,
      sector_offset=sector_offset, byte_offset=byte_offset, parse_vss=parse_vss,
      vss_stores=vss_stores)
