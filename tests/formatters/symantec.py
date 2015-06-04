#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Symantec AV log file event formatter."""

import unittest

from plaso.formatters import symantec

from tests.formatters import test_lib


class SymantecAVFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Symantec AV log file event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = symantec.SymantecAVFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = symantec.SymantecAVFormatter()

    expected_attribute_names = [
        u'event_map',
        u'category_map',
        u'virus',
        u'file',
        u'action0_map',
        u'action1_map',
        u'action2_map',
        u'description',
        u'scanid',
        u'event_data',
        u'remote_machine',
        u'remote_machine_ip']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
