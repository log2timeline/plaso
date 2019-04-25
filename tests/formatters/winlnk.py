#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Shortcut (LNK) event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winlnk

from tests.formatters import test_lib


class WinLnkLinkFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Windows Shortcut (LNK) event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = winlnk.WinLnkLinkFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = winlnk.WinLnkLinkFormatter()

    expected_attribute_names = [
        'description', 'file_size', 'file_attribute_flags', 'drive_type',
        'drive_serial_number', 'volume_label', 'local_path',
        'network_path', 'command_line_arguments', 'env_var_location',
        'relative_path', 'working_directory', 'icon_location',
        'link_target']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
