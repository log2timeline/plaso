#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""Tests for the Mac OS X local users plist plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import plist as plist_formatter
from plaso.lib import event
from plaso.lib import timelib_test
from plaso.parsers import plist
from plaso.parsers.plist_plugins import macuser
from plaso.parsers.plist_plugins import test_lib


class MacUserPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Mac OS X local user plist plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = macuser.MacUserPlugin(None)
    pre_obj = event.PreprocessObject()
    self._parser = plist.PlistParser(pre_obj)

  def testProcess(self):
    """Tests the Process function."""
    plist_name = u'user.plist'
    test_file = self._GetTestFilePath([plist_name])
    events = self._ParsePlistFileWithPlugin(
        self._parser, self._plugin, test_file, plist_name)
    event_objects = self._GetEventObjects(events)

    self.assertEquals(len(event_objects), 1)

    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-12-28 04:35:47')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.key, u'passwordLastSetTime')
    self.assertEqual(event_object.root, u'/')
    expected_desc = (
        u'Last time user (501) changed the password: '
        u'$ml$37313$fa6cac1869263baa85cffc5e77a3d4ee164b7'
        u'5536cae26ce8547108f60e3f554$a731dbb0e386b169af8'
        u'9fbb33c255ceafc083c6bc5194853f72f11c550c42e4625'
        u'ef113b66f3f8b51fc3cd39106bad5067db3f7f1491758ff'
        u'e0d819a1b0aba20646fd61345d98c0c9a411bfd1144dd4b'
        u'3c40ec0f148b66d5b9ab014449f9b2e103928ef21db6e25'
        u'b536a60ff17a84e985be3aa7ba3a4c16b34e0d1d2066ae178')
    self.assertEqual(event_object.desc, expected_desc)
    expected_string = u'//passwordLastSetTime {}'.format(expected_desc)
    expected_short = u'{}...'.format(expected_string[:77])
    self._TestGetMessageStrings(
        event_object, expected_string, expected_short)


if __name__ == '__main__':
  unittest.main()
