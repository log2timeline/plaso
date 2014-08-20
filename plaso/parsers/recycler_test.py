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
"""Tests for the Windows recycler parsers."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import recycler as recycler_formatter
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers import recycler
from plaso.parsers import test_lib


class WinRecycleBinParserTest(test_lib.ParserTestCase):
  """Tests for the Windows Recycle Bin parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = recycler.WinRecycleBinParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['$II3DF3L.zip'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 1)

    event_object = event_objects[0]

    self.assertEquals(event_object.orig_filename, (
        u'C:\\Users\\nfury\\Documents\\Alloy Research\\StarFury.zip'))

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2012-03-12 20:49:58.633')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(event_object.file_size, 724919)

    expected_msg = (
        u'C:\\Users\\nfury\\Documents\\Alloy Research\\StarFury.zip '
        u'(from drive C?)')
    expected_msg_short = (
        u'Deleted file: C:\\Users\\nfury\\Documents\\Alloy Research\\'
        u'StarFury.zip')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


class WinRecyclerInfo2ParserTest(test_lib.ParserTestCase):
  """Tests for the Windows Recycler INFO2 parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = recycler.WinRecycleInfo2Parser()

  def testParse(self):
    """Reads an INFO2 file and run a few tests."""
    test_file = self._GetTestFilePath(['INFO2'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 4)

    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2004-08-25 16:18:25.237')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.DELETED_TIME)

    self.assertEquals(event_object.index, 1)
    self.assertEquals(event_object.orig_filename, (
        u'C:\\Documents and Settings\\Mr. Evil\\Desktop\\lalsetup250.exe'))

    event_object = event_objects[1]

    expected_msg = (
        u'DC2 -> C:\\Documents and Settings\\Mr. Evil\\Desktop'
        u'\\netstumblerinstaller_0_4_0.exe [C:\\Documents and '
        u'Settings\\Mr. Evil\\Desktop\\netstumblerinstaller_0_4_0.exe] '
        u'(from drive C)')
    expected_msg_short = (
        u'Deleted file: C:\\Documents and Settings\\Mr. Evil\\Desktop'
        u'\\netstumblerinstaller...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[2]

    self._TestGetSourceStrings(event_object, u'Recycle Bin', u'RECBIN')


if __name__ == '__main__':
  unittest.main()
