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

from plaso.collector import interface
from plaso.collector import os_helper
from plaso.lib import event
from plaso.lib import storage_helper
from plaso.lib import utils
from plaso.parsers import filestat


class OSCollector(interface.Collector):
  """Class that implements a collector object that uses os."""

  def __init__(
      self, process_queue, output_queue, directory, add_dir_stat=True):
    """Initializes the collector object.

    Args:
      proces_queue: The files processing queue (instance of
                    queue.QueueInterface).
      output_queue: The event output queue (instance of queue.QueueInterface).
                    This queue is used as a buffer to the storage layer.
      directory: Path to the directory that contains the files to be collected.
      add_dir_stat: Optional boolean value to indicate whether or not we want to
                    include directory stat information into the storage queue.
                    The default is true.
    """
    super(OSCollector, self).__init__(
        process_queue, output_queue, add_dir_stat=add_dir_stat)
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

    directory_stat = os_helper.GetOsDirectoryStat(path)
    storage_helper.SendContainerToStorage(
        filestat.GetEventContainerFromStat(directory_stat),
        directory_stat, self._storage_queue)

  def ProcessFile(self, filename):
    """Finds all files available inside a file and inserts into queue."""
    transfer_proto = event.EventPathSpec()
    transfer_proto.type = 'OS'
    transfer_proto.file_path = utils.GetUnicodeString(filename)
    self._queue.Queue(transfer_proto.ToProtoString())
