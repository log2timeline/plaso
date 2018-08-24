#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the santa file event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import santa

from tests.formatters import test_lib


class SantaExecutionFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the santa execution event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = santa.SantaExecutionFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = santa.SantaExecutionFormatter()

    expected_attribute_names = [
        'decision',
        'process_path',
        'process_hash'
    ]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

    # TODO: add test for GetMessages.


class SantaFileSystemFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the santa file operation event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = santa.SantaFileSystemFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = santa.SantaFileSystemFormatter()

    expected_attribute_names = [
        'action',
        'file_path',
        'process_path'
    ]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

    # TODO: add test for GetMessages.


class SantaDiskMountsFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the santa disk mounts event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = santa.SantaDiskMountsFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = santa.SantaDiskMountsFormatter()

    expected_attribute_names = [
        'action',
        'mount',
        'serial',
        'dmg_path']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

    # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
