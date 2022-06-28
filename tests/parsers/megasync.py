#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MEGASync log parser."""

import unittest

from plaso.parsers import megasync
from plaso.lib import errors
from tests.parsers import test_lib

class MEGASyncLogUnitTest(test_lib.ParserTestCase):
    """Tests for the MEGASync log parser."""

    def testVerifyStructure(self):
      """Tests for the VerifyStructure method"""
      mediator = None
      parser = megasync.MEGASyncParser()

      valid_lines = (
          '01/21-08:24:53.632258 7988 INFO Transfer (UPLOAD) starting. File: sample.txt [megaapi_impl.cpp:16786]',
          '[repeated x5]'
      )
      for line in valid_lines:
        self.assertTrue(parser.VerifyStructure(mediator, line))

      invalid_lines = (
          '01/21-08:24:53.632258 INFO Transfer (UPLOAD) starting. File: sample.txt [megaapi_impl.cpp:16786]',
          '01/21-08:24:53.632258 7988 BADLEVEL Transfer (UPLOAD) starting. File: sample.txt [megaapi_impl.cpp:16786]',
          '1999/01/21-08:24:53.632258 7988 INFO Transfer (UPLOAD) starting. File: sample.txt [megaapi_impl.cpp:16786]',
      )
      for line in invalid_lines:
        self.assertFalse(parser.VerifyStructure(mediator, line))

    def testParseLog(self):
      """Tests the Parse function on the MEGASync log"""
      parser = megasync.MEGASyncParser()
      storage_writer = self._ParseFile(['megasync.log'], parser)

      number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
      self.assertEqual(number_of_events, 4)

      number_of_extraction_warnings = storage_writer.GetNumberOfAttributeContainers(
          'extraction_warning')
      self.assertEqual(number_of_extraction_warnings, 0)

      number_of_recovery_warnings = storage_writer.GetNumberOfAttributeContainers(
          'recovery_warning')
      self.assertEqual(number_of_recovery_warnings, 0)

      events = list(storage_writer.GetSortedEvents())

      expected_event_values = {
          'date_time': '2022-01-21 08:24:53',
          'log_level': 'DBG',
          'message': 'Activating transfer [megaclient.cpp:4092]',
      }

      self.CheckEventValues(storage_writer, events[0], expected_event_values)

      expected_event_values = {
          'date_time': '2022-01-21 08:24:53',
          'log_level': 'INFO',
          'message': 'Transfer (UPLOAD) starting. File: sample.txt [megaapi_impl.cpp:16786]',
      }

      self.CheckEventValues(storage_writer, events[1], expected_event_values)

      expected_event_values = {
          'date_time': '2022-01-21 08:24:54',
          'log_level': 'DBG',
          'message': r'Creating thumb/preview for C:\Test\Path\New directory\sample.txt [gfx.cpp:297]',
      }

      self.CheckEventValues(storage_writer, events[2], expected_event_values)

      expected_event_values = {
          'date_time': '2022-01-21 08:24:55',
          'log_level': 'INFO',
          'message': 'Transfer (UPLOAD) finished. File: sample.txt [megaapi_impl.cpp:16370]',
      }

      self.CheckEventValues(storage_writer, events[3], expected_event_values)


if __name__ == '__main__':
  unittest.main()