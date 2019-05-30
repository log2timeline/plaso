#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Keychain password database parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import mac_keychain as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers import mac_keychain

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class MacKeychainParserTest(test_lib.ParserTestCase):
  """Tests for keychain file parser."""

  @shared_test_lib.skipUnlessHasTestFile(['login.keychain'])
  def testParse(self):
    """Tests the Parse function."""
    parser = mac_keychain.KeychainParser()
    storage_writer = self._ParseFile(['login.keychain'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 8)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2014-01-26 14:51:48.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    self.assertEqual(event.entry_name, 'Secret Application')
    self.assertEqual(event.account_name, 'moxilo')
    expected_ssgp = (
        'b8e44863af1cb0785b89681d22e2721997ccfb8adb8853e726aff94c8830b05a')
    self.assertEqual(event.ssgp_hash, expected_ssgp)
    expected_message = 'Name: Secret Application Account: moxilo'
    expected_short_message = 'Secret Application'
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[1]

    self.assertEqual(
        event.timestamp_desc,
        definitions.TIME_DESCRIPTION_MODIFICATION)

    self.CheckTimestamp(event.timestamp, '2014-01-26 14:52:29.000000')

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2014-01-26 14:53:29.000000')

    self.assertEqual(event.entry_name, 'Secret Note')
    self.assertEqual(event.text_description, 'secure note')
    self.assertEqual(len(event.ssgp_hash), 1696)
    expected_message = 'Name: Secret Note'
    expected_short_message = 'Secret Note'
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[4]

    self.CheckTimestamp(event.timestamp, '2014-01-26 14:54:33.000000')

    self.assertEqual(event.entry_name, 'plaso.kiddaland.net')
    self.assertEqual(event.account_name, 'MrMoreno')
    expected_ssgp = (
        '83ccacf55a8cb656d340ec405e9d8b308fac54bb79c5c9b0219bd0d700c3c521')
    self.assertEqual(event.ssgp_hash, expected_ssgp)
    self.assertEqual(event.where, 'plaso.kiddaland.net')
    self.assertEqual(event.protocol, 'http')
    self.assertEqual(event.type_protocol, 'dflt')

    expected_message = (
        'Name: plaso.kiddaland.net '
        'Account: MrMoreno '
        'Where: plaso.kiddaland.net '
        'Protocol: http (dflt)')
    expected_short_message = 'plaso.kiddaland.net'
    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
