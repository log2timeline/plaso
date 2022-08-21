#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows shell item custom event formatter helpers."""

import unittest

from plaso.formatters import shell_items

from tests.formatters import test_lib


class ShellItemFileEntryNameFormatterHelperTest(
    test_lib.EventFormatterTestCase):
  """Tests for the Windows shell item file entry name formatter helper."""

  def testFormatEventValues(self):
    """Tests the FormatEventValues function."""
    formatter_helper = shell_items.ShellItemFileEntryNameFormatterHelper()

    output_mediator = self._CreateOutputMediator()

    event_values = {
        'long_name': 'long',
        'name': 'short'}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['file_entry_name'], 'long')

    event_values = {
        'long_name': None,
        'name': 'short'}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['file_entry_name'], 'short')

    event_values = {
        'long_name': None,
        'name': None}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertIsNone(event_values['file_entry_name'])


if __name__ == '__main__':
  unittest.main()
