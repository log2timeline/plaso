#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Shortcut (LNK) custom event formatter helpers."""

import unittest

from plaso.formatters import winlnk

from tests.formatters import test_lib


class WindowsShortcutLinkedPathFormatterHelperTest(
    test_lib.EventFormatterTestCase):
  """Tests for the Windows Shortcut (LNK) linked path formatter helper."""

  def testFormatEventValues(self):
    """Tests the FormatEventValues function."""
    formatter_helper = winlnk.WindowsShortcutLinkedPathFormatterHelper()

    output_mediator = self._CreateOutputMediator()

    event_values = {
        'local_path': 'local',
        'network_path': 'network',
        'relative_path': 'relative',
        'working_directory': 'cwd'}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['linked_path'], 'local')

    event_values = {
        'local_path': None,
        'network_path': 'network',
        'relative_path': 'relative',
        'working_directory': 'cwd'}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['linked_path'], 'network')

    event_values = {
        'local_path': None,
        'network_path': None,
        'relative_path': 'relative',
        'working_directory': 'cwd'}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['linked_path'], 'cwd\\relative')

    event_values = {
        'local_path': None,
        'network_path': None,
        'relative_path': 'relative',
        'working_directory': None}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['linked_path'], 'relative')

    event_values = {
        'local_path': None,
        'network_path': None,
        'relative_path': None,
        'working_directory': None}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['linked_path'], 'Unknown')


if __name__ == '__main__':
  unittest.main()
