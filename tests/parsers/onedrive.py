#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Microsoft OneDrive log file parser."""

import unittest

from plaso.parsers import onedrive

from tests.parsers import test_lib


class OneDriveTest(test_lib.ParserTestCase):
  """Tests the OneDrive log file parser."""

  _AES_KEY = (
        b'\xe5\x06\x02\x00\xa3\x07\xbc\xa8'
        b'\x04\x77\xf7\xf1\x33\x10\x73\xb7'
        b'\xb2\xfc\x52\x05\xcb\xb1\xdf\x3b'
        b'\xd0\xc7\x98\x8f\x4e\x5f\x8c\xed')

  _RAW_PARAMETER_DATA_BYTES = (
      b'n\x01\x00\x00pnQNrDddt8-OpipvhdqEoA:\\'
      b'tv99OFuY_KXMMwlQaXTSjQ\\agYrXq28vbJnPpFW_BXEkA\\'
      b'7Wkdl_bsbhXjgy3mxq5yEg\\'
      b'-SHZdzOU0wA0iP5IsARudt0nSV1LvPW6JoOIFzce_Ck\\'
      b'8rCHT9NIvsVDQFxNxEN3tg\\ZKekHDq5ByJMCunDdo7QHw\\'
      b'-Od38zWspQ0v9xeoHHteiQ\\'
      b'LBn1U6SqmvuW-I7vXWfWyRXY7PXItZbDbj7fy52ubH0\\'
      b'3jxHZ1c8WaPczE8XdVpS9A\\aOYl9sH9CRI3lU4XSyMpwg\\'
      b'GrwrivqnY-LdeR-N5W9Hqw\\'
      b'gWnvkJWs277FUkYsqPUHiOedbvQSoMBRQj-u_CotLVk.cpp'
      b'\x1e\x00\x00\x00CWnpConnManager::AsyncGetProxy'
      b'\xad\x00\x00\x00\x0e\xda\x04\x80')

  def testParseODLGZFile(self):
    """Tests parsing a compressed OneDrive log file."""
    parser = onedrive.OneDriveLogFileParser()

    storage_writer = self._ParseFile([
        'SyncEngine-2022-11-24.2341.10688.1.odlgz'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 3038)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_event_data, 0)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_event_data, 0)

    expected_event_values = {
        'data_type': 'windows:onedrive:log',
        'code_filename': 'SyncServiceProxy.cpp',
        'code_function_name':
        'SyncServiceProxy::OnDownloadedSelectiveSyncEntries',
        'decoded_parameters': [
            'test document.docx', 'Document', 'B201A0178F192B2B!107',
            'B201A0178F192B2B!107.10', 'B201A0178F192B2B!101'],
        'raw_parameters':
            (b'\x10\x00\x00\x00TaxRagRight.docx\x08\x00\x00\x00Document\x14\x00'
             b'\x00\x00B201A0178F192B2B!107\x17\x00\x00\x00B201A0178F192B2B!107'
             b'.10\x14\x00\x00\x00B201A0178F192B2B!101\x00'.hex()),
        'recorded_time': '2022-11-24T23:41:48.678+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2700)
    self.CheckEventData(event_data, expected_event_values)

  def test_encrypted_parameters_data(self):
    """Tests the _ProcessRawParameters method with encrypted parameter data."""
    parser = onedrive.OneDriveLogFileParser()

    # pylint: disable=protected-access
    extracted_strings = parser._ProcessRawParameters(
        self._RAW_PARAMETER_DATA_BYTES,
        aes_key=self._AES_KEY, obfuscated_string_map=None)

    self.assertEqual(extracted_strings, [
        ('K:\\dbs\\sh\\odct\\1017_210557\\cmd\\2\\client\\'
         'onedrive\\Product\\wns\\trans\\WnpConnManager.cpp'),
        'CWnpConnManager::AsyncGetProxy'])


if __name__ == '__main__':
  unittest.main()
