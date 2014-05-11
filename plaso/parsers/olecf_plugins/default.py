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
"""The default plugin for parsing OLE Compound Files (OLECF)."""

from plaso.lib import event
from plaso.lib import eventdata

from plaso.parsers.olecf_plugins import interface


class OleCfItemEvent(event.FiletimeEvent):
  """Convenience class for an OLECF item event."""

  DATA_TYPE = 'olecf:item'

  def __init__(self, timestamp, usage, olecf_item):
    """Initializes the event.

    Args:
      timetamp: The FILETIME timestamp value.
      usage: A string describing the timestamp value.
      olecf_item: The OLECF item (pyolecf.item).
    """
    super(OleCfItemEvent, self).__init__(timestamp, usage)

    # TODO: need a better way to express the original location of the
    # original data.
    self.offset = 0

    self.name = olecf_item.name
    # TODO: have pyolecf return the item type here.
    # self.type = olecf_item.type
    self.size = olecf_item.size


class DefaultOleCFPlugin(interface.OlecfPlugin):
  """The default OLE CF file behavior."""

  NAME = 'olecf_default'

  def Process(self, root_item=None, item_names=None, **kwargs):
    """Determine if this is the right plugin for this OLECF file.

    This function takes a list of sub items found in the root of a
    OLECF file and compares that to a list of required items defined
    in this plugin.

    If the list of required items is a subset of the overall items
    this plugin is considered to be the correct plugin and the function
    will return back a generator that yields event objects.

    Args:
      root_item: The root item of the OLECF file.
      item_names: A list of all items discovered in the root.

    Returns:
      A generator that yields event objects.

    Raises:
      errors.WrongPlugin: If the set of required items is not a subset
      of the available items.
      ValueError: If the root_item or items are not set.
    """
    if root_item is None or item_names is None:
      raise ValueError(u'Root item or items are not set.')

    return self.GetEntries(root_item=root_item)

  def _ParseItem(self, olecf_item):
    creation_time, modification_time = self.GetTimestamps(olecf_item)

    if creation_time:
      yield OleCfItemEvent(
          creation_time, eventdata.EventTimestamp.CREATION_TIME, olecf_item)

    if modification_time:
      yield OleCfItemEvent(
          modification_time, eventdata.EventTimestamp.MODIFICATION_TIME,
          olecf_item)

    for sub_item in olecf_item.sub_items:
      for sub_event_object in self._ParseItem(sub_item):
        yield sub_event_object

  def GetEntries(self, root_item, **unused_kwargs):
    """Yields an event object for every entry."""
    record_yielded = False
    for event_object in self._ParseItem(root_item):
      yield event_object
      record_yielded = True

    # If no record has been created, let's add one in.
    if not record_yielded:
      yield OleCfItemEvent(
          0, eventdata.EventTimestamp.CREATION_TIME, root_item)
