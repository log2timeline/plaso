# -*- coding: utf-8 -*-
"""Tests for the networkminer log file event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import networkminer

from tests.formatters import test_lib

class NetworkMinerFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the networkminer log file event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = networkminer.NetworkminerEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = networkminer.NetworkminerEventFormatter()

    expected_attribute_names = [
        'event_map',
        'category_map',
        'virus',
        'file',
        'action0_map',
        'action1_map',
        'action2_map',
        'description',
        'scanid',
        'event_data',
        'remote_machine',
        'remote_machine_ip']

    #self._TestGetFormatStringAttributeNames(
     #   event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
