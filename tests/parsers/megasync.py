#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MEGASync log parser."""

import unittest

from plaso.parsers import megasync
from tests.parsers import test_lib

class MEGASyncLogUnitTest(test_lib.ParserTestCase):
  """Tests for the MEGASync log parser."""

  def testParseLog(self):
    """Tests the Parse function on the MEGASync log"""
    parser = megasync.MEGASyncParser()

    storage_writer = self._ParseFile(
        ['MEGAsync.1'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 799)

    # 2 extremely long lines in the test sample. 
    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'date_time': '2022-08-09 21:26:37.511525',
        'log_level': 'INFO',
        'message': ('Transfer (UPLOAD) starting. '
            'File: document.txt [megaapi_impl.cpp:16564]'),
    }

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'date_time': '2022-08-09 21:26:37.512274',
        'log_level': 'DBG',
        'message': ('Creating thumb/preview for '
            '/Users/testinguser/image.jpg [gfx.cpp:291]'),
    }

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'date_time': '2022-08-09 21:26:38.656322',
        'log_level': 'DBG',
        'message': ('Upload complete: '
            'image.jpg 1 [transfer.cpp:990]'),
    }

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'date_time': '2022-08-09 21:26:38.713318',
        'log_level': 'DBG',
        'message': ('Upload complete: '
            'document.txt 1 [transfer.cpp:990]'),
    }

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'date_time': '2022-08-09 21:26:39.462363',
        'log_level': 'INFO',
        'message': ('Transfer (UPLOAD) finished. '
            'File: image.jpg [megaapi_impl.cpp:16161]'),
    }

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'date_time': '2022-08-09 21:27:08.238282',
        'log_level': 'WARN',
        'message': ('Transfer (UPLOAD) finished with error: '
            'Read error File: aggr_state [megaapi_impl.cpp:16151]'),
    }

    self.CheckEventValues(storage_writer, events[788], expected_event_values)


if __name__ == '__main__':
  unittest.main()
