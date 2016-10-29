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
    parser_object = opera.OperaTypedHistoryParser()
    storage_writer = self._ParseFile([u'typed_history.xml'], parser_object)

    self.assertEqual(len(storage_writer.events), 4)

    event_object = storage_writer.events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-11 23:45:27')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(event_object.entry_selection, u'Filled from autocomplete.')

    expected_string = u'plaso.kiddaland.net (Filled from autocomplete.)'

    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = storage_writer.events[3]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-11 22:46:07')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(event_object.entry_selection, u'Manually typed.')

    expected_string = u'theonion.com (Manually typed.)'

    self._TestGetMessageStrings(event_object, expected_string, expected_string)


class OperaGlobalParserTest(test_lib.ParserTestCase):
  """Tests for the Opera Global History parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'global_history.dat'])
  def testParseFile(self):
    """Read a history file and run a few tests."""
    parser_object = opera.OperaGlobalHistoryParser()
    storage_writer = self._ParseFile([u'global_history.dat'], parser_object)

    self.assertEqual(len(storage_writer.events), 37)

    event_object = storage_writer.events[4]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-11 22:45:46')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'http://www.mbl.is/frettir/erlent/2013/11/11/'
        u'karl_bretaprins_faer_ellilifeyri/ (Karl Bretaprins fær ellilífeyri'
        u' - mbl.is) [First and Only Visit]')
    expected_msg_short = (
        u'http://www.mbl.is/frettir/erlent/2013/11/11/'
        u'karl_bretaprins_faer_ellilifeyri/...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = storage_writer.events[10]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-11 22:45:55')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    event_object = storage_writer.events[16]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-11 22:46:16')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_title = (
        u'10 Celebrities You Never Knew Were Abducted And Murdered '
        u'By Andie MacDowell | The Onion - America\'s Finest News Source')

    self.assertEqual(event_object.title, expected_title)


if __name__ == '__main__':
  unittest.main()
