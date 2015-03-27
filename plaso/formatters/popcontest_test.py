#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Popularity Contest event formatters."""

import unittest

from plaso.formatters import popcontest
from plaso.formatters import test_lib


class PopularityContestSessionFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the PCAP event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = popcontest.PopularityContestSessionFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = popcontest.PopularityContestSessionFormatter()

    expected_attribute_names = [
        u'session',
        u'status',
        u'hostid',
        u'details']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class PopularityContestLogFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the PCAP event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = popcontest.PopularityContestLogFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = popcontest.PopularityContestLogFormatter()

    expected_attribute_names = [
        u'mru',
        u'package',
        u'record_tag']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
