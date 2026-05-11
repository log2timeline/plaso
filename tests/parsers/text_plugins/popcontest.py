#!/usr/bin/env python3
"""Tests for the Popularity Contest (popcontest) text parser plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import popcontest

from tests.parsers.text_plugins import test_lib


class PopularityContestTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the Popularity Contest (popcontest) text parser plugin."""

  def testCheckRequiredFormat(self):
    """Tests for the CheckRequiredFormat function."""
    plugin = popcontest.PopularityContestTextPlugin()
    parser_mediator = parsers_mediator.ParserMediator()

    file_object = io.BytesIO(
        b'POPULARITY-CONTEST-0 TIME:1277185301 '
        b'ID:12345678901234567890123456789012 ARCH:i386 POPCONVER:1.38\n')
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    self.assertTrue(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    # Check non-matching format.
    file_object = io.BytesIO(
        b'Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new '
        b'content in image.dd.\n')
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

  def testProcess(self):
    """Tests the Process function."""
    plugin = popcontest.PopularityContestTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['popcontest1.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 12)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'access_time': '2010-06-22T07:34:42+00:00',
        'change_time': '2010-04-06T12:25:42+00:00',
        'data_type': 'linux:popularity_contest_log:entry',
        'mru': '/usr/sbin/atd',
        'package': 'at'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'linux:popularity_contest_log:session',
        'end_time': '2010-06-22T05:41:41+00:00',
        'details': 'ARCH:i386 POPCONVER:1.38',
        'host_identifier': '12345678901234567890123456789012',
        'session': 0,
        'start_time': '2010-06-22T05:41:41+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 6)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
