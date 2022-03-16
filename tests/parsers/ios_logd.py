#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the iOS Mobile Installation log parser."""

import unittest

from plaso.parsers import ios_logd

from tests.parsers import test_lib


class IOSysdiagnoseLogdUnitTest(test_lib.ParserTestCase):
  """Tests for the Logd log parser"""

  def testParseLog(self):
    """Tests the Parse function."""
    parser = ios_logd.IOSysdiagnoseLogdParser()
    storage_writer = self._ParseFile(['logd.0.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 76)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'timestamp': '2021-08-10 22:50:23.000000',
        'logger': 'logd[29]',
        'body': 'libtrace_kic=1'
    }

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'timestamp': '2021-10-13 04:41:02.000000',
        'logger': 'logd_helper[90]',
        'body': 'Harvesting: 9227BC73-2AF5-318F-AA62-DCBE2219DBC8'
        }

    self.CheckEventValues(storage_writer, events[29], expected_event_values)


if __name__ == '__main__':
  unittest.main()
