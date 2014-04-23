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
"""Tests for the OLE Compound File (OLECF) default plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import olecf as olecf_formatter
from plaso.lib import event
from plaso.lib import eventdata

from plaso.parsers.olecf_plugins import interface
from plaso.parsers.olecf_plugins import default
from plaso.parsers.olecf_plugins import test_lib


class TestOleCfDefaultPlugin(test_lib.OleCfPluginTestCase):
  """Tests for the OLECF default plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    self._plugin = default.DefaultOleCFPlugin(pre_obj)

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath(['Document.doc'])
    event_generator = self._ParseOleCfFileWithPlugin(test_file, self._plugin)
    event_containers = self._GetEventContainers(event_generator)
    self.assertEquals(len(event_containers), 3)

    # Check the Root Entry event.
    event_container = event_containers[0]

    self.assertEquals(len(event_container.events), 1)
    self.assertEquals(event_container.name, u'Root Entry')

    event_object = event_container.events[0]

    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.MODIFICATION_TIME)
    # May 16, 2013 02:29:49.795000000 UTC.
    self.assertEquals(event_object.timestamp, 1368671389795000)

    expected_string = (
        u'Name: Root Entry')

    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    # Check one other entry.
    event_container = event_containers[1]
    event_object = event_container.events[0]

    expected_string = u'Name: MsoDataStore'
    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    # date -u -d "2013-05-16T02:29:49" +"%s.%N"
    self.assertEquals(event_object.timestamp, 1368671389704000)


if __name__ == '__main__':
  unittest.main()
