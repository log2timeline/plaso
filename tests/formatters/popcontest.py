#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Popularity Contest event formatters."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import popcontest

from tests.formatters import test_lib


class PopularityContestSessionFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the PCAP event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = popcontest.PopularityContestSessionFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = popcontest.PopularityContestSessionFormatter()

    expected_attribute_names = [
        'session',
        'status',
        'hostid',
        'details']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class PopularityContestLogFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the PCAP event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = popcontest.PopularityContestLogFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = popcontest.PopularityContestLogFormatter()

    expected_attribute_names = [
        'mru',
        'package',
        'record_tag']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
