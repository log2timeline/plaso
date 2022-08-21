#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the file system event formatters."""

import unittest

from plaso.formatters import file_system

from tests.formatters import test_lib


class NTFSFileReferenceFormatterHelperTest(test_lib.EventFormatterTestCase):
  """Tests for the NTFS file reference formatter helper."""

  def testFormatEventValues(self):
    """Tests the FormatEventValues function."""
    formatter_helper = file_system.NTFSFileReferenceFormatterHelper()

    output_mediator = self._CreateOutputMediator()

    event_values = {'file_reference': 0x2000000000011 }
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['file_reference'], '17-2')

    event_values = {'file_reference': None}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertIsNone(event_values['file_reference'])


class NTFSParentFileReferenceFormatterHelperTest(
    test_lib.EventFormatterTestCase):
  """Tests for the NTFS parent file reference formatter helper."""

  def testFormatEventValues(self):
    """Tests the FormatEventValues function."""
    formatter_helper = file_system.NTFSParentFileReferenceFormatterHelper()

    output_mediator = self._CreateOutputMediator()

    event_values = {'parent_file_reference': 0x2000000000011 }
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['parent_file_reference'], '17-2')

    event_values = {'parent_file_reference': None}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertIsNone(event_values['parent_file_reference'])


class NTFSPathHintsFormatterHelper(test_lib.EventFormatterTestCase):
  """Tests for the NTFS path hints formatter helper."""

  def testFormatEventValues(self):
    """Tests the FormatEventValues function."""
    formatter_helper = file_system.NTFSPathHintsFormatterHelper()

    output_mediator = self._CreateOutputMediator()

    event_values = {'path_hints': ['path1', 'path2']}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertEqual(event_values['path_hints'], 'path1;path2')

    event_values = {'path_hints': None}
    formatter_helper.FormatEventValues(output_mediator, event_values)
    self.assertIsNone(event_values['path_hints'])


if __name__ == '__main__':
  unittest.main()
