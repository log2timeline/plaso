#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Opera browser history parsers."""

import unittest

from plaso.formatters import opera  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import opera

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class OperaTypedParserTest(test_lib.ParserTestCase):
  """Tests for the Opera Typed History parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'typed_history.xml'])
  def testParse(self):
    """Tests the Parse function."""
    parser = opera.OperaTypedHistoryParser()
    storage_writer = self._ParseFile([u'typed_history.xml'], parser)

    self.assertEqual(storage_writer.number_of_events, 4)

    events = list(storage_writer.GetEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-11 23:45:27')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(event.entry_selection, u'Filled from autocomplete.')

    expected_string = u'plaso.kiddaland.net (Filled from autocomplete.)'

    self._TestGetMessageStrings(event, expected_string, expected_string)

    event = events[3]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-11 22:46:07')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(event.entry_selection, u'Manually typed.')

    expected_string = u'theonion.com (Manually typed.)'

    self._TestGetMessageStrings(event, expected_string, expected_string)


class OperaGlobalParserTest(test_lib.ParserTestCase):
  """Tests for the Opera Global History parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'global_history.dat'])
  def testParseFile(self):
    """Read a history file and run a few tests."""
    parser = opera.OperaGlobalHistoryParser()
    storage_writer = self._ParseFile([u'global_history.dat'], parser)

    self.assertEqual(storage_writer.number_of_events, 37)

    events = list(storage_writer.GetEvents())

    event = events[4]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-11 22:45:46')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'http://www.mbl.is/frettir/erlent/2013/11/11/'
        u'karl_bretaprins_faer_ellilifeyri/ (Karl Bretaprins fær ellilífeyri'
        u' - mbl.is) [First and Only Visit]')
    expected_short_message = (
        u'http://www.mbl.is/frettir/erlent/2013/11/11/'
        u'karl_bretaprins_faer_ellilifeyri/...')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[10]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-11 22:45:55')
    self.assertEqual(event.timestamp, expected_timestamp)

    event = events[16]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-11 22:46:16')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_title = (
        u'10 Celebrities You Never Knew Were Abducted And Murdered '
        u'By Andie MacDowell | The Onion - America\'s Finest News Source')

    self.assertEqual(event.title, expected_title)


if __name__ == '__main__':
  unittest.main()
