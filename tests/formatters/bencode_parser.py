#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the bencode parser event formatters."""

import unittest

from plaso.formatters import bencode_parser

from tests.formatters import test_lib


class TransmissionEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Apple System Log (ASL) log event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = bencode_parser.TransmissionEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = bencode_parser.TransmissionEventFormatter()

    expected_attribute_names = [
        u'destination', u'seedtime']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class UTorrentEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Apple System Log (ASL) log event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = bencode_parser.UTorrentEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = bencode_parser.UTorrentEventFormatter()

    expected_attribute_names = [
        u'caption', u'path', u'seedtime']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
