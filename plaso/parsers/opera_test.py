#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Opera browser history parsers."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import opera as opera_formatter
from plaso.lib import timelib_test
from plaso.parsers import opera
from plaso.parsers import test_lib


class OperaTypedParserTest(test_lib.ParserTestCase):
  """Tests for the Opera Typed History parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = opera.OperaTypedHistoryParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['typed_history.xml'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 4)

    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-11-11 23:45:27')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(event_object.entry_selection, 'Filled from autocomplete.')

    expected_string = u'plaso.kiddaland.net (Filled from autocomplete.)'

    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = event_objects[3]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-11-11 22:46:07')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(event_object.entry_selection, 'Manually typed.')

    expected_string = u'theonion.com (Manually typed.)'

    self._TestGetMessageStrings(event_object, expected_string, expected_string)


class OperaGlobalParserTest(test_lib.ParserTestCase):
  """Tests for the Opera Global History parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = opera.OperaGlobalHistoryParser()

  def testParseFile(self):
    """Read a history file and run a few tests."""
    test_file = self._GetTestFilePath(['global_history.dat'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 37)

    event_object = event_objects[4]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-11-11 22:45:46')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'http://www.mbl.is/frettir/erlent/2013/11/11/'
        u'karl_bretaprins_faer_ellilifeyri/ (Karl Bretaprins fær ellilífeyri'
        u' - mbl.is) [First and Only Visit]')
    expected_msg_short = (
        u'http://www.mbl.is/frettir/erlent/2013/11/11/'
        u'karl_bretaprins_faer_ellilifeyri/...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[10]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-11-11 22:45:55')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    event_object = event_objects[16]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-11-11 22:46:16')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    expected_title = (
        u'10 Celebrities You Never Knew Were Abducted And Murdered '
        u'By Andie MacDowell | The Onion - America\'s Finest News Source')

    self.assertEquals(event_object.title, expected_title)


if __name__ == '__main__':
  unittest.main()
