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
"""The operating system collector object implementation."""

import logging
import os
import re

from plaso.collector import interface
from plaso.collector import os_helper
from plaso.lib import collector_filter
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import storage_helper
from plaso.lib import utils
from plaso.parsers import filestat
from plaso.pvfs import pfile_entry
from plaso.pvfs import utils as pvfs_utils


class OSCollector(interface.PfileCollector):
  """Class that implements a pfile-based collector object that uses os."""

  def __init__(self, process_queue, output_queue, source_path):
    """Initializes the collector object.

    Args:
      proces_queue: The files processing queue (instance of
                    queue.QueueInterface).
      output_queue: The event output queue (instance of queue.QueueInterface).
                    This queue is used as a buffer to the storage layer.
      source_path: Path of the source file or directory.
    """
    super(OSCollector, self).__init__(process_queue, output_queue)
    self._filter_file_path = None
    self._pre_obj = None
    self._source_path = source_path

  def _CopyPathToPathSpec(self, path):
    """Copies the path to a path specification equivalent.""" 
    path_spec = event.EventPathSpec()
    path_spec.type = 'OS'
    path_spec.file_path = utils.GetUnicodeString(path)
    return path_spec

  def _ProcessDirectory(self, file_entry):
    """Processes a directory and extract its metadata if necessary."""
    for sub_file_entry in file_entry.GetSubFileEntries():
      if sub_file_entry.IsLink():
        continue

      if sub_file_entry.IsDirectory():
        if self.collect_directory_metadata:
          # TODO: solve this differently by putting the path specification
          # on the queue and have the filestat parser just extract the metadata.
          stat_object = sub_file_entry.Stat()
          stat_object.full_path = sub_file_entry.pathspec.file_path
          stat_object.display_path = sub_file_entry.pathspec.file_path
          storage_helper.SendContainerToStorage(
              filestat.GetEventContainerFromStat(stat_object), stat_object,
              self._storage_queue)
        self._ProcessDirectory(sub_file_entry)

      elif sub_file_entry.IsFile():
        self._queue.Queue(sub_file_entry.pathspec.ToProtoString())

  def _ProcessFilter(self):
    """Processes the source path based on the collection filter."""
    preprocessor_collector = FileSystemPreprocessCollector(
        self._pre_obj, self._source_path)
    filter_object = collector_filter.CollectionFilter(
        preprocessor_collector, self._filter_file_path)

    for pathspec_string in filter_object.GetPathSpecs():
      self._queue.Queue(pathspec_string)

  def SetFilter(self, filter_file_path, pre_obj):
    """Sets the collection filter.

    Args:
      filter_file_path: The path of the filter file.
      pre_obj: The preprocessor object.
    """
    self._filter_file_path = filter_file_path
    self._pre_obj = pre_obj

  def Collect(self):
    """Collects files from the source path."""
    source_path_spec = self._CopyPathToPathSpec(self._source_path)
    source_file_entry = pfile_entry.OsFileEntry(source_path_spec)

    if not source_file_entry.IsDirectory() and not source_file_entry.IsFile():
      raise errors.CollectorError(
          u'Source path: {0:s} not a file or directory.'.format(
              self._source_path))

    if self._filter_file_path:
      self._ProcessFilter()

    elif source_file_entry.IsDirectory():
      self._ProcessDirectory(source_file_entry)

    else:
      self._queue.Queue(source_path_spec.ToProtoString())


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
    """Return a list of files given a path and a pattern.

    Args:
      path: the path.
      file_name: the file name pattern.

    Returns:
      A list of file names.
    """
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
    except OSError as exception:
      logging.error(
          u'Unable to read directory: {0:s}, reason {1:s}'.format(
              directory, exception))
    return ret

  def OpenFileEntry(self, path):
    """Opens a file entry object from the path."""
    return pvfs_utils.OpenOSFileEntry(os.path.join(self._mount_point, path))

  def ReadingFromImage(self):
    """Indicates if the collector is reading from an image file."""
    return False


