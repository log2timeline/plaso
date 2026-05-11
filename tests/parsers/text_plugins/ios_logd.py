#!/usr/bin/env python3
"""Tests for the iOS sysdiagnose logd files (logd.0.log) text parser plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import ios_logd

from tests.parsers.text_plugins import test_lib


class IOSSysdiagnoseLogdUnitTest(test_lib.TextPluginTestCase):
  """Tests for the iOS sysdiagnose logd files (logd.0.log) text plugin."""

  def testCheckRequiredFormat(self):
    """Tests for the CheckRequiredFormat function."""
    plugin = ios_logd.IOSSysdiagnoseLogdTextPlugin()
    parser_mediator = parsers_mediator.ParserMediator()

    file_object = io.BytesIO(
        b'2021-08-11 05:50:23-0700 logd_helper[85]: Migrating: '
        b'"/private/var/db/diagnostics/timesync"\n')
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
    plugin = ios_logd.IOSSysdiagnoseLogdTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['logd.0.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 76)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'body': 'libtrace_kic=1',
        'data_type': 'ios:sysdiagnose:logd:line',
        'logger': 'logd[29]',
        'written_time': '2021-08-11T05:50:23-07:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
