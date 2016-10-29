#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Popularity Contest (popcontest) parser."""

import unittest

from plaso.formatters import popcontest  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import popcontest

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class PopularityContestUnitTest(test_lib.ParserTestCase):
  """Tests for the popcontest parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'popcontest1.log'])
  def testParse(self):
    """Tests the Parse function."""
    parser_object = popcontest.PopularityContestParser()
    storage_writer = self._ParseFile([u'popcontest1.log'], parser_object)

    self.assertEqual(len(storage_writer.events), 22)

    event_object = storage_writer.events[0]

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ADDED_TIME)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-06-22 05:41:41')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_string = (
        u'Session 0 start '
        u'ID 12345678901234567890123456789012 [ARCH:i386 POPCONVER:1.38]')
    expected_short_string = u'Session 0 start'
    self._TestGetMessageStrings(
        event_object, expected_string, expected_short_string)

    event_object = storage_writer.events[1]

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-06-22 07:34:42')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_string = u'mru [/usr/sbin/atd] package [at]'
    expected_short_string = u'/usr/sbin/atd'
    self._TestGetMessageStrings(
        event_object, expected_string, expected_short_string)

    event_object = storage_writer.events[3]

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-06-22 07:34:43')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_string = (
        u'mru [/usr/lib/python2.5/lib-dynload/_struct.so] '
        u'package [python2.5-minimal]')
    expected_short_string = u'/usr/lib/python2.5/lib-dynload/_struct.so'
    self._TestGetMessageStrings(
        event_object, expected_string, expected_short_string)

    event_object = storage_writer.events[5]

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-05-30 05:26:20')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_string = (
        u'mru [/usr/bin/empathy] package [empathy] tag [RECENT-CTIME]')
    expected_short_string = u'/usr/bin/empathy'
    self._TestGetMessageStrings(
        event_object, expected_string, expected_short_string)

    event_object = storage_writer.events[6]

    self.assertEqual(
        event_object.timestamp_desc,
        eventdata.EventTimestamp.ENTRY_MODIFICATION_TIME)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-05-30 05:27:43')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_string = (
        u'mru [/usr/bin/empathy] package [empathy] tag [RECENT-CTIME]')
    expected_short_string = u'/usr/bin/empathy'
    self._TestGetMessageStrings(
        event_object, expected_string, expected_short_string)

    event_object = storage_writer.events[11]

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-05-12 07:58:33')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_string = u'mru [/usr/bin/orca] package [gnome-orca] tag [OLD]'
    expected_short_string = u'/usr/bin/orca'
    self._TestGetMessageStrings(
        event_object, expected_string, expected_short_string)

    event_object = storage_writer.events[13]

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ADDED_TIME)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-06-22 05:41:41')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_string = u'Session 0 end'
    expected_short_string = expected_string
    self._TestGetMessageStrings(
        event_object, expected_string, expected_short_string)

    event_object = storage_writer.events[14]

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ADDED_TIME)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-06-22 05:41:41')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_string = (
        u'Session 1 start '
        u'ID 12345678901234567890123456789012 [ARCH:i386 POPCONVER:1.38]')
    expected_short_string = u'Session 1 start'
    self._TestGetMessageStrings(
        event_object, expected_string, expected_short_string)

    event_object = storage_writer.events[15]

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-06-22 07:34:42')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_string = u'mru [/super/cool/plasuz] package [plaso]'
    expected_short_string = u'/super/cool/plasuz'
    self._TestGetMessageStrings(
        event_object, expected_string, expected_short_string)

    event_object = storage_writer.events[18]

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-04-06 12:25:42')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_string = u'mru [/super/cool/plasuz] package [miss_ctime]'
    expected_short_string = u'/super/cool/plasuz'
    self._TestGetMessageStrings(
        event_object, expected_string, expected_short_string)

    event_object = storage_writer.events[19]

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-05-12 07:58:33')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_string = u'mru [/super/cóól] package [plaso] tag [WRONG_TAG]'
    expected_short_string = u'/super/cóól'
    self._TestGetMessageStrings(
        event_object, expected_string, expected_short_string)

    event_object = storage_writer.events[21]

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ADDED_TIME)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-06-22 05:41:41')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_string = u'Session 1 end'
    expected_short_string = expected_string
    self._TestGetMessageStrings(
        event_object, expected_string, expected_short_string)


if __name__ == '__main__':
  unittest.main()
