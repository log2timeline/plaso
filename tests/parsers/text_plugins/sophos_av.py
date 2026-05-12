#!/usr/bin/env python3
"""Tests for the Sophos Anti-Virus log (SAV.txt) text parser plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import sophos_av

from tests.parsers.text_plugins import test_lib


class SophosAVLogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the Sophos Anti-Virus log (SAV.txt) text parser plugin."""

  def testCheckRequiredFormat(self):
    """Tests for the CheckRequiredFormat function."""
    plugin = sophos_av.SophosAVLogTextPlugin()
    parser_mediator = parsers_mediator.ParserMediator()

    file_object = io.BytesIO(
        b'20100720 183814 File "C:\\Documents and '
        b'Settings\\Administrator\\Desktop\\sxl_test_50.com" belongs to '
        b'virus/spyware \'LiveProtectTest\'.\n')
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
    plugin = sophos_av.SophosAVLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['sav.txt'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'added_time': '2010-07-20T18:38:14',
        'data_type': 'sophos:av:log',
        'text': (
            'File "C:\\Documents and Settings\\Administrator\\Desktop\\'
            'sxl_test_50.com" belongs to virus/spyware \'LiveProtectTest\'.')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
