#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Viminfo parser."""

import unittest

from plaso.parsers import viminfo

from tests.parsers import test_lib


class ViminfoUnitTest(test_lib.ParserTestCase):
  """Tests for the Viminfo parser."""

  # pylint: disable=protected-access

  def testParse(self):
    """Tests the Parse function."""
    parser = viminfo.VimInfoParser()
    storage_writer = self._ParseFile(['.viminfo'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 10)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'date_time': '2009-02-13 23:31:30',
        'data_type': 'viminfo:history',
        'type': 'Command Line History',
        'value': 'e TEST',
        'item_number': 0}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
