#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
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
"""Parser related functions and classes for testing."""

import unittest

from plaso.lib import event
from plaso.lib import eventdata
from plaso.pvfs import pfile
from plaso.pvfs import utils as pvfs_utils


class ParserTestCase(unittest.TestCase):
  """The unit test case for a parser."""

  def _GetEventContainer(self, events):
    """Retrieves the event container from the events returned by the parser.

       This function expects that there is only 1 event container in the events.
  
    Args:
      events: a list of events containers or objects as returned by the parser
              (instances of EventObject or EventContainer).

    Returns:
      A list of event objects (instances of EventObject).
    """
    self.assertEquals(len(events), 1)

    event_container = events[0]
    self.assertIsInstance(event_container, event.EventContainer)

    return event_container

  def _GetEventContainers(self, events):
    """Retrieves the event containers from the events returned by the parser.
  
       This function does not allow for nested event event containers.

    Args:
      events: a list of events containers or objects as returned by the parser
              (instances of EventObject or EventContainer).

    Returns:
      A list of event containers (instances of EventContainer).
    """
    event_containers = []

    for event_container in events:
      self.assertIsInstance(event_container, event.EventContainer)
      self.assertNotEquals(event_container.containers, None)
      event_containers.append(event_container)

    return event_containers

  def _GetEventObjects(self, events):
    """Retrieves the event objects from the events returned by the parser.
  
       This function will extract events objects from event containers. It
       does not allow for nested event event containers.

    Args:
      events: a list of events containers or objects as returned by the parser
              (instances of EventObject or EventContainer).

    Returns:
      A list of event objects (instances of EventObject).
    """
    event_objects = []

    for event_object in events:
      if isinstance(event_object, event.EventContainer):
        self.assertNotEquals(event_object.containers, None)

        event_objects.extend(event_object.events)
      else:
        event_objects.append(event_object)

    for event_object in event_objects:
      self.assertIsInstance(event_object, event.EventObject)

    return event_objects

  def _ParseFile(self, parser_object, filename):
    """Parses a file using the parser class.
  
    Args:
      parser_object: the parser object.
      filename: the name of the file to parse.

    Returns:
      A list of event containers or objects as returned by the parser
      (instances of EventObject or EventContainer).
    """
    file_entry = pvfs_utils.OpenOSFileEntry(filename)
    return list(parser_object.Parse(file_entry))

  def _ParseFileByPathSpec(self, parser_object, path_spec, fscache=None):
    """Parses a file using the parser class.

    Args:
      parser_object: the parser object.
      path_spect: the path specification of the file to parse.
      fscache: optional file system cache object. The default is None.

    Returns:
      A list of event containers or objects as returned by the parser
      (instances of EventObject or EventContainer).
    """
    file_entry = pfile.OpenPFileEntry(path_spec, fscache=fscache)
    return list(parser_object.Parse(file_entry))

  def _TestGetMessageStrings(
      self, event_object, expected_msg, expected_msg_short):
    """Tests the formatting of the message strings.

       This function invokes the GetMessageStrings function of the event
       formatter on the event object and compares the resulting messages
       strings with those expected.

    Args:
      event_object: the event object (instance of EventObject).
      expected_msg: the expected message string.
      expected_msg_shor: the expected short message string.
    """
    msg, msg_short = eventdata.EventFormatterManager.GetMessageStrings(
        event_object)
    self.assertEquals(msg, expected_msg)
    self.assertEquals(msg_short, expected_msg_short)
