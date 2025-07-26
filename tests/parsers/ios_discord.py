#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Discord message log parser."""

import unittest

from plaso.parsers import ios_discord
from tests.parsers import test_lib


class DiscordParserTest(test_lib.ParserTestCase):
  """Tests for the Discord message log parser."""

  def testParseFile(self):
    """Tests parsing a Discord message log file."""
    parser = ios_discord.IOSDiscordParser()
    storage_writer = self._ParseFile(
      ['23AAD8D4-D632-4F99-8E44-152AAB8FA9D6'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 26)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Testing a message containing content
    # and not containing attachment_proxy_urls.
    expected_event_values = {
      'channel_identifier': '622810296226152474',
      'content': 'That was painful to watch.',
      'sent_time': '2023-04-24T18:17:21.655000+00:00',
      'user_identifier': '579257851646574644',
      'username': 'josh_hickman1',}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Testing a message not containing content
    # and containing attachment_proxy_urls.
    expected_event_values = {
      'attachment_name': 'IMG_1953.jpg',
      'attachment_proxy_url': 'https://media.discordapp.net/attachments/'
        '622810296226152474/1041012392089370735/IMG_1953.jpg',
      'attachment_size': 2149749,
      'attachment_type': 'image/jpeg',
      'channel_identifier': '622810296226152474',
      'content': None,
      'sent_time': '2022-11-12T15:31:35.458000+00:00',
      'user_identifier': '579257851646574644',
      'username': 'josh_hickman1',}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 10)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
