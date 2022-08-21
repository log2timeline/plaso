#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Prefetch event formatter."""

import unittest

from plaso.formatters import winprefetch

from tests.formatters import test_lib


class WindowsPrefetchPathHintsFormatterHelperTest(
    test_lib.EventFormatterTestCase):
  """Tests for the Windows Prefetch path hints formatter helper."""

  def testFormatEventValues(self):
    """Tests the FormatEventValues function."""
    formatter_helper = winprefetch.WindowsPrefetchPathHintsFormatterHelper()

    output_mediator = self._CreateOutputMediator()

    event_values = {'path_hints': ['path1', 'path2']}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['path_hints'], 'path1; path2')

    event_values = {'path_hints': None}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertIsNone(event_values['path_hints'])


class WindowsPrefetchVolumesStringFormatterHelperTest(
    test_lib.EventFormatterTestCase):
  """Tests for the Windows Prefetch volumes string formatter helper."""

  def testFormatEventValues(self):
    """Tests the FormatEventValues function."""
    formatter_helper = winprefetch.WindowsPrefetchVolumesStringFormatterHelper()

    output_mediator = self._CreateOutputMediator()

    expected_volumes_string = (
        'volume: 1 [serial number: 0x12345678, device path: device1]')

    event_values = {
        'number_of_volumes': 1,
        'volume_device_paths': ['device1'],
        'volume_serial_numbers': [0x12345678]}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['volumes_string'], expected_volumes_string)

    expected_volumes_string = (
        'volume: 1 [serial number: UNKNOWN, device path: device1]')

    event_values = {
        'number_of_volumes': 1,
        'volume_device_paths': ['device1'],
        'volume_serial_numbers': None}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['volumes_string'], expected_volumes_string)

    expected_volumes_string = (
        'volume: 1 [serial number: 0x12345678, device path: UNKNOWN]')

    event_values = {
        'number_of_volumes': 1,
        'volume_device_paths': None,
        'volume_serial_numbers': [0x12345678]}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['volumes_string'], expected_volumes_string)

    event_values = {
        'number_of_volumes': 0,
        'volume_device_paths': None,
        'volume_serial_numbers': None}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertNotIn('volumes_string', event_values)


if __name__ == '__main__':
  unittest.main()
