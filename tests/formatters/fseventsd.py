#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the fseventsd record event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import fseventsd
from plaso.parsers import fseventsd as fseventsd_parser

from tests.formatters import test_lib


class FseventsdFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the fseventsd record event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = fseventsd.FSEventsdEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = fseventsd.FSEventsdEventFormatter()

    expected_attribute_names = [
        'object_type', 'path', 'event_types', 'event_identifier']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  def testGetMessages(self):
    """Tests the GetMessages method."""
    formatter = fseventsd.FSEventsdEventFormatter()

    event_data = fseventsd_parser.FseventsdEventData()
    event_data.flags = 0x80000001
    event_data.event_identifier = 47747061
    event_data.path = '.Spotlight-V100/Store-V1'
    event = self._CreateTestEvent(event_data)
    expected_message = (
        'Folder: .Spotlight-V100/Store-V1 Changes: FolderCreated Event ID: '
        '47747061')
    expected_short_message = '.Spotlight-V100/Store-V1 FolderCreated'
    self._TestGetMessages(
        event, formatter, expected_message, expected_short_message)

  # TODO: add test for GetSources.


if __name__ == '__main__':
  unittest.main()
