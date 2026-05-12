#!/usr/bin/env python3
"""Tests for the vsftpd log file text parser plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import vsftpd

from tests.parsers.text_plugins import test_lib


class VsftpdLogTextPluginText(test_lib.TextPluginTestCase):
  """Tests for the vsftpd log file text parser plugin."""

  def testCheckRequiredFormat(self):
    """Tests for the CheckRequiredFormat function."""
    plugin = vsftpd.VsftpdLogTextPlugin()
    parser_mediator = parsers_mediator.ParserMediator()

    file_object = io.BytesIO(
        b'Mon Jun  6 18:43:28 2016 [pid 2] CONNECT: Client "192.168.1.9"\n')
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
    plugin = vsftpd.VsftpdLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['vsftpd.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 25)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'added_time': '2016-06-10T14:24:19',
        'data_type': 'vsftpd:log',
        'text': (
            '[pid 3] [jean] OK DOWNLOAD: Client "192.168.1.7", '
            '"/home/jean/trains/how-thomas-the-tank-engine-works-1.jpg", '
            '49283 bytes, 931.38Kbyte/sec')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 12)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
