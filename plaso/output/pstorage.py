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
"""Implements a StorageFile output formatter."""

from plaso.lib import event
from plaso.lib import output
from plaso.lib import storage
from plaso.lib import timelib


class Pstorage(output.LogOutputFormatter):
  """Dumps event objects to a plaso storage file."""

  def Start(self):
    """Sets up the output storage file."""
    pre_obj = event.PreprocessObject()
    pre_obj.collection_information = {'time_of_run': timelib.Timestamp.GetNow()}
    if hasattr(self._config, 'filter') and self._config.filter:
      pre_obj.collection_information['filter'] = self._config.filter
    if hasattr(self._config, 'storagefile') and self._config.storagefile:
      pre_obj.collection_information[
          'file_processed'] = self._config.storagefile
    self._storage = storage.StorageFile(self.filehandle, pre_obj=pre_obj)

  def EventBody(self, event_object):
    """Add an EventObject protobuf to the storage file.

    Args:
      proto: The EventObject protobuf.
    """
    # Needed due to duplicate removals, if two events
    # are merged then we'll just pick the first inode value.
    inode = getattr(event_object, 'inode', None)
    if type(inode) in (str, unicode):
      inode_list = inode.split(';')
      try:
        new_inode = int(inode_list[0])
      except (ValueError, IndexError):
        new_inode = 0

      event_object.inode = new_inode

    self._storage.AddEventObject(event_object)

  def End(self):
    """Closes the storage file."""
    self._storage.Close()
