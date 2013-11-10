#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""Tests for the Android SMS parser."""
import os
import unittest

# pylint: disable-msg=W0611
from plaso.formatters import android_sms as android_sms_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import android_sms

import pytz


class AndroidSmsTest(unittest.TestCase):
  """Tests for the Android SMS database parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC

    self.test_parser = android_sms.AndroidSmsParser(pre_obj)

  def testParseFile(self):
    """Read an Android SMS mmssms.db file and run a few tests."""
    test_file = os.path.join('test_data', 'mmssms.db')

    events = None
    with open(test_file, 'rb') as file_object:
      events = list(self.test_parser.Parse(file_object))

    # The SMS database file contains 9 events (5 SENT, 4 RECEIVED messages).
    self.assertEquals(len(events), 9)

    # Check the first SMS sent.
    event_object = events[0]

    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.CREATION_TIME)

    # date -u -d"2013-10-29 16:56:28.038000" +"%s.%N"
    self.assertEquals(event_object.timestamp, 1383065788038 * 1000)

    expected_address = '1 555-521-5554'
    self.assertEquals(event_object.address, expected_address)

    expected_body = 'Yo Fred this is my new number.'
    self.assertEquals(event_object.body, expected_body)

    # Test the event specific formatter.
    msg, short = eventdata.EventFormatterManager.GetMessageStrings(
         event_object)

    expected_msg = (
        u'Type: SENT '
        u'Address: 1 555-521-5554 '
        u'Status: READ '
        u'Message: Yo Fred this is my new number.')
    expected_short = u'Yo Fred this is my new number.'
    self.assertEquals(msg, expected_msg)
    self.assertEquals(short, expected_short)


if __name__ == '__main__':
  unittest.main()
