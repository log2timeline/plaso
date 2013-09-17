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
"""Tests for the LS Quarantine database parser."""
import os
import unittest

# pylint: disable-msg=W0611
from plaso.formatters import ls_quarantine as dummy_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import ls_quarantine

import pytz


class LSQuarantineParserTest(unittest.TestCase):
  """Tests for the LS Quarantine parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC

    self.test_parser = ls_quarantine.LsQuarantineParser(pre_obj)

  def testParseFile(self):
    """Read a test LS Quarantine database."""
    test_file = os.path.join('test_data', 'quarantine.db')

    events = None
    with open(test_file, 'rb') as file_object:
      events = list(self.test_parser.Parse(file_object))

    # The quarantine DB contains 14 events.
    self.assertEquals(len(events), 14)

    # Verify few entries.
    vlc_event = events[3]
    mackeeper_event = events[9]
    speedtest_event = events[10]

    # date -u -d"Jul 08, 2013 21:12:03" +"%s%N" (divided by 1000).
    self.assertEquals(vlc_event.timestamp, 1373317923000000)

    # date -u -d"Jul 12, 2013 19:28:58" +"%s%N"
    self.assertEquals(mackeeper_event.timestamp, 1373657338000000)

    # date -u -d"Jul 12, 2013 19:30:16" +"%s%N"
    self.assertEquals(speedtest_event.timestamp, 1373657416000000)

    self.assertEquals(vlc_event.agent, 'Google Chrome')
    vlc_url = (
        'http://download.cnet.com/VLC-Media-Player/3001-2139_4-10210434.html'
        '?spi=40ab24d3c71594a5017d74be3b0c946c')
    self.assertEquals(vlc_event.url, vlc_url)

    self.assertTrue('vlc-2.0.7-intel64.dmg' in vlc_event.data)

    speedtest_message = (
        '[Google Chrome] Downloaded: http://mackeeperapp.zeobit.com/aff/'
        'speedtest.net.6/download.php?affid=460245286&trt=5&utm_campaign='
        '3ES&tid_ext=P107fSKcSfqpMbcP3sI4fhKmeMchEB3dkAGpX4YIsvM;US;L;1 '
        '<http://download.mackeeper.zeobit.com/package.php?'
        'key=460245286&trt=5&landpr=Speedtest>')
    message_string, _ = eventdata.EventFormatterManager.GetMessageStrings(
        speedtest_event)
    self.assertEquals(message_string, speedtest_message)


if __name__ == '__main__':
  unittest.main()
