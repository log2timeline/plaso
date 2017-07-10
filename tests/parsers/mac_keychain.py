#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Keychain password database parser."""

import unittest

from plaso.formatters import mac_keychain  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import mac_keychain

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class MacKeychainParserTest(test_lib.ParserTestCase):
  """Tests for keychain file parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'login.keychain'])
  def testParse(self):
    """Tests the Parse function."""
    parser = mac_keychain.KeychainParser()
    storage_writer = self._ParseFile([u'login.keychain'], parser)

    self.assertEqual(storage_writer.number_of_events, 8)

    events = list(storage_writer.GetEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-01-26 14:51:48')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    self.assertEqual(event.entry_name, u'Secret Application')
    self.assertEqual(event.account_name, u'moxilo')
    expected_ssgp = (
        u'b8e44863af1cb0785b89681d22e2721997ccfb8adb8853e726aff94c8830b05a')
    self.assertEqual(event.ssgp_hash, expected_ssgp)
    self.assertEqual(event.text_description, u'N/A')
    expected_message = u'Name: Secret Application Account: moxilo'
    expected_short_message = u'Secret Application'
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[1]

    self.assertEqual(
        event.timestamp_desc,
        definitions.TIME_DESCRIPTION_MODIFICATION)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-01-26 14:52:29')
    self.assertEqual(event.timestamp, expected_timestamp)

    event = events[2]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-01-26 14:53:29')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.entry_name, u'Secret Note')
    self.assertEqual(event.text_description, u'secure note')
    self.assertEqual(len(event.ssgp_hash), 1696)
    expected_message = u'Name: Secret Note'
    expected_short_message = u'Secret Note'
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[4]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-01-26 14:54:33')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.entry_name, u'plaso.kiddaland.net')
    self.assertEqual(event.account_name, u'MrMoreno')
    expected_ssgp = (
        u'83ccacf55a8cb656d340ec405e9d8b308fac54bb79c5c9b0219bd0d700c3c521')
    self.assertEqual(event.ssgp_hash, expected_ssgp)
    self.assertEqual(event.where, u'plaso.kiddaland.net')
    self.assertEqual(event.protocol, u'http')
    self.assertEqual(event.type_protocol, u'dflt')
    self.assertEqual(event.text_description, u'N/A')

    expected_message = (
        u'Name: plaso.kiddaland.net '
        u'Account: MrMoreno '
        u'Where: plaso.kiddaland.net '
        u'Protocol: http (dflt)')
    expected_short_message = u'plaso.kiddaland.net'
    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
