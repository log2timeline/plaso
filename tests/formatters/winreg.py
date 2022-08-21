#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Registry custom event formatter helpers."""

import unittest

from plaso.formatters import winreg

from tests.formatters import test_lib


class WindowsRegistryValuesFormatterHelperTest(
    test_lib.EventFormatterTestCase):
  """Tests for the Windows Registry values formatter helper."""

  def testFormatEventValues(self):
    """Tests the FormatEventValues function."""
    formatter_helper = winreg.WindowsRegistryValuesFormatterHelper()

    output_mediator = self._CreateOutputMediator()

    event_values = {'values': 'value1, value2'}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['values'], 'value1, value2')

    event_values = {'values': None}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['values'], '(empty)')


if __name__ == '__main__':
  unittest.main()
