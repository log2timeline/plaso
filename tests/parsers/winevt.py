#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows EventLog (EVT) parser."""

import unittest

from plaso.parsers import winevt

from tests.parsers import test_lib


class WinEvtParserTest(test_lib.ParserTestCase):
  """Tests for the Windows EventLog (EVT) parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = winevt.WinEvtParser()
    storage_writer = self._ParseFile(['SysEvent.Evt'], parser)

    # Windows Event Log (EVT) information:
    #	Version                     : 1.1
    #	Number of records           : 6063
    #	Number of recovered records : 438
    #	Log type                    : System

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 6501)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Event number      : 1392
    # Creation time     : Jul 27, 2011 06:41:47 UTC
    # Written time      : Jul 27, 2011 06:41:47 UTC
    # Event type        : Warning event (2)
    # Computer name     : WKS-WINXP32BIT
    # Source name       : LSASRV
    # Event category    : 3
    # Event identifier  : 0x8000a001 (2147524609)
    # Number of strings : 2
    # String: 1         : cifs/CONTROLLER
    # String: 2         : "The system detected a possible attempt to compromise
    #                     security. Please ensure that you can contact the
    #                     server that authenticated you.\r\n (0xc0000388)"

    expected_event_values = {
        'creation_time': '2011-07-27T06:41:47+00:00',
        'computer_name': 'WKS-WINXP32BIT',
        'data_type': 'windows:evt:record',
        'event_category': 3,
        'event_identifier': 40961,
        'event_type': 2,
        'record_number': 1392,
        'severity': 2,
        'source_name': 'LSASRV',
        'strings': ['cifs/CONTROLLER', (
            '"The system detected a possible attempt to compromise security. '
            'Please ensure that you can contact the server that authenticated '
            'you.\r\n (0xc0000388)"')],
        'written_time': '2011-07-27T06:41:47+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
