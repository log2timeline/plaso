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
"""File for PyVFS migration to contain all OS specific collector code."""

import logging
import os

from plaso.lib import collector
from plaso.lib import collector_filter
from plaso.lib import event
from plaso.lib import os_preprocess
from plaso.lib import pfile
from plaso.lib import utils
from plaso.parsers import filestat


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


class SimpleFileCollector(collector.Collector):
  """This is a simple collector that collects from a directory."""

  def __init__(self, proc_queue, stor_queue, directory, dir_stat=True):
    """Initialize the file collector.

    Args:
      proc_queue: A Plaso queue object used as a processing queue of files.
      stor_queue: A Plaso queue object used as a buffer to the storage layer.
      directory: Path to the directory that contains files to be collected.
      dir_stat: A boolean that determines whether or not we want to include
      directory stat information into the storage queue.
    """
    super(SimpleFileCollector, self).__init__(proc_queue, stor_queue, dir_stat)
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
    if not self._dir_stat:
      return

    directory_stat = GetOsDirectoryStat(path)
    collector.SendContainerToStorage(
        filestat.GetEventContainerFromStat(directory_stat),
        directory_stat, self._storage_queue)

  def ProcessFile(self, filename):
    """Finds all files available inside a file and inserts into queue."""
    transfer_proto = event.EventPathSpec()
    transfer_proto.type = 'OS'
    transfer_proto.file_path = utils.GetUnicodeString(filename)
    self._queue.Queue(transfer_proto.ToProtoString())


class TargetedFileSystemCollector(SimpleFileCollector):
  """This is a simple collector that collects using a targeted list."""

  def __init__(
      self, proc_queue, stor_queue, pre_obj, mount_point, file_filter,
      dir_stat=True):
    """Initialize the targeted filesystem collector.

    Args:
      proc_queue: A Plaso queue object used as a processing queue of files.
      stor_queue: A Plaso queue object used as a buffer to the storage layer.
      pre_obj: The PlasoPreprocess object.
      mount_point: The path to the mount point or base directory.
      file_filter: The path of the filter file.
      dir_stat: A boolean that determines whether or not we want to include
      directory stat information into the storage queue.
    """
    super(TargetedFileSystemCollector, self).__init__(
        proc_queue, stor_queue, mount_point, dir_stat)
    self._collector = os_preprocess.FileSystemCollector(
        pre_obj, mount_point)
    self._file_filter = file_filter

  def Collect(self):
    """Start the collector."""
    for pathspec_string in collector_filter.CollectionFilter(
        self._collector, self._file_filter).GetPathSpecs():
      self._queue.Queue(pathspec_string)
