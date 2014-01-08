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
"""Tests for the Symantec AV Log parser."""

import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import symantec as symantec_formatter
from plaso.lib import preprocess
from plaso.parsers import symantec
from plaso.parsers import test_lib

import pytz


class SymantecAccessProtectionUnitTest(test_lib.ParserTestCase):
  """Tests for the Symantec AV Log parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC
    self._parser = symantec.SymantecParser(pre_obj, None)
    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    self.maxDiff = None

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['Symantec.Log'])
    events = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(events)

    # The file contains 8 lines which should result in 8 event objects.
    self.assertEquals(len(event_objects), 8)

    # Test the second entry:
    event_object = event_objects[1]

    self.assertEquals(event_object.timestamp, 1354272449000000)
    self.assertEquals(event_object.user, u'davnads')
    expected_file = (
        u'D:\\Twinkle_Prod$\\VM11 XXX\\outside\\test.exe.txt')
    self.assertEquals(event_object.file, expected_file)

    expected_msg = (
        u'Event Name: GL_EVENT_INFECTION; '
        u'Category Name: GL_CAT_INFECTION; '
        u'Malware Name: W32.Changeup!gen33; '
        u'Malware Path: '
        u'D:\\Twinkle_Prod$\\VM11 XXX\\outside\\test.exe.txt; '
        u'Action0: Unknown; '
        u'Action1: Clean virus from file; '
        u'Action2: Delete infected file; '
        u'Scan ID: 0; '
        u'Event Data: 201\t4\t6\t1\t65542\t0\t0\t0\t0\t0\t0')
    expected_msg_short = (
        u'D:\\Twinkle_Prod$\\VM11 XXX\\outside\\test.exe.txt; '
        u'W32.Changeup!gen33; '
        u'Unknown; ...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
