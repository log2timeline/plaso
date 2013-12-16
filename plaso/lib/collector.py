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

from plaso.lib import utils


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


class Collector(object):
  """An interface for file collection in Plaso."""

  def __init__(self, proc_queue, stor_queue, dir_stat=True):
    """Initialize the Collector.

    The collector takes care of discovering all the files that need to be
    processed. Once a file is discovered it is described using a EventPathSpec
    object and inserted into a processing queue.

    Args:
      proc_queue: A Plaso queue object used as a processing queue of files.
      stor_queue: A Plaso queue object used as a buffer to the storage layer.
      dir_stat: A boolean that determines whether or not we want to include
      directory stat information into the storage queue.
    """
    self._queue = proc_queue
    self._storage_queue = stor_queue
    self._dir_stat = dir_stat

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
