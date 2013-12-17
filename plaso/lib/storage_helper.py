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
"""The storage helper functions."""

from plaso.lib import utils


def SendContainerToStorage(event_container, stat, storage_queue):
  """Read events from a event container and send them to storage.

  Args:
    event_container: The event container object (instance of
                     event.EventContainer).
    stat: A stat object (instance of pfile.Stats).
    storage_queue: The storage queue to send extracted events to.
  """
  for event_object in event_container:
    event_object.filename = getattr(stat, 'full_path', '<unknown>')
    event_object.display_name = getattr(
        stat, 'display_path', event_object.filename)
    event_object.parser = u'PfileStatParser'
    event_object.inode = utils.GetInodeValue(stat.ino)
    storage_queue.AddEvent(event_object.ToProtoString())
