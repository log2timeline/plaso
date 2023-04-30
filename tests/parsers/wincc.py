#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests the for bodyfile parser."""

import unittest

from plaso.parsers import wincc

from tests.parsers import test_lib


class SIMATICTest(test_lib.ParserTestCase):
  """Tests for the SIMATIC S7 logs parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = wincc.SIMATICLogParser()
    storage_writer = self._ParseFile(
        ['wincc_simatic_s7_proto_suite.log'], parser)
    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 284)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'wincc:simatic_s7:entry',
        'creation_time': '2019-05-27T10:05:43+00:00',
        'body': ('419 INFO     | LogFileCount  : 3')
    }
    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)


class WinCCSyslogTest(test_lib.ParserTestCase):
  """Tests for the Wincc sys logs parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = wincc.WinCCSysLogParser()
    storage_writer = self._ParseFile(
        ['wincc_sys.log'], parser)
    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 768)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'wincc:sys_log:entry',
        'log_identifier': 2303,
        'creation_time': '2019-05-27T10:10:04.712',
        'event_number': 1012301,
        'log_hostname': 'BMS001',
        'source_device': 'CCWriteArchiveServer',
        'body': ('[(null) 224]failed to insert into MSARCLONG with '
                 '0x80004005(#0 \'2019-05-27 08:10:03.602\') MSG_STATE_COME')
    }
    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
