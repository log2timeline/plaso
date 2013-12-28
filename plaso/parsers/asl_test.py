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
"""Parser test for Apple System Log files."""

import os
import pytz
import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import asl as asl_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import asl
from plaso.parsers import test_lib


class AslParserTest(unittest.TestCase):
  """The unit test for ASL parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC

    self._parser = asl.AslParser(pre_obj, None)

  def testParse(self):
    """Tests the Parse function."""
    test_file = os.path.join('test_data', 'applesystemlog.asl')

    events = test_lib.ParseFile(self._parser, test_file)

    self.assertEqual(len(events), 2)

    event = events[0]

    # date -u -d"Wed, 13 Nov 2013 17:52:34" +"%s705481"
    self.assertEqual(1385372735705481, event.timestamp)
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(event)
    expected_msg = ('MessageID: 101406 Level: WARNING (4) User ID: 205 '
                   'Group ID: 205 Read User: 205 Read Group: ALL Host: '
                   'DarkTemplar-2.local Sender: locationd Facility: '
                   'com.apple.locationd Message: Incorrect '
                   'NSStringEncoding value 0x8000100 detected. '
                   'Assuming NSASCIIStringEncoding. Will stop this '
                   'compatiblity mapping behavior in the near future. '
                   '[CFLog Local Time: 2013-11-25 09:45:35.701][CFLog '
                   'Thread: 1007][Sender_Mach_UUID: '
                   '50E1F76A-60FF-368C-B74E-EB48F6D98C51]')
    self.assertEqual(expected_msg, msg)
    self.assertEqual(442, event.record_position)
    self.assertEqual(101406, event.message_id)
    self.assertEqual('DarkTemplar-2.local', event.computer_name)
    self.assertEqual('locationd', event.sender)
    self.assertEqual('com.apple.locationd', event.facility)
    self.assertEqual(69, event.pid)
    self.assertEqual(205, event.user_sid)
    self.assertEqual(205, event.group_id)
    self.assertEqual(205, event.read_uid)
    self.assertEqual('ALL', event.read_gid)
    self.assertEqual('WARNING (4)', event.level)
    expected_message = ('Incorrect NSStringEncoding value 0x8000100 '
                        'detected. Assuming NSASCIIStringEncoding. '
                        'Will stop this compatiblity mapping behavior '
                        'in the near future.')
    self.assertEqual(expected_message, event.message)
    expected_extra_1 = '[CFLog Local Time: 2013-11-25 09:45:35.701]'
    expected_extra_2 = '[CFLog Thread: 1007]'
    expected_extra_3 = ('[Sender_Mach_UUID: '
                        '50E1F76A-60FF-368C-B74E-EB48F6D98C51]')
    expected_extra = expected_extra_1 + expected_extra_2 + expected_extra_3
    self.assertEqual(expected_extra, event.extra_information)


if __name__ == '__main__':
  unittest.main()
