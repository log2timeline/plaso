#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Apple Unified Logging parser."""

import csv
import glob
import logging
import tempfile
import os
import re
import subprocess
import unittest

from pathlib import Path

from plaso.parsers import aul

from plaso.helpers.mac import dns

from tests.parsers import test_lib


class AULParserTest(test_lib.ParserTestCase):
  """Tests for the AUL parser."""

  def testSpecialParsing(self):
    """Tests the Parse function on a Special tracev3."""
    parser = aul.AULParser()
    storage_writer = self._ParseFile([
      'AUL', 'private', 'var', 'db', 'Diagnostics', 'Special',
      '0000000000000001.tracev3'
    ], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event_data')
    self.assertEqual(number_of_events, 12154)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'mac:aul:event',
        'creation_time': '2023-01-12T01:36:27.111432704+00:00',
        'level': 'Default',
        'subsystem': 'com.apple.SkyLight',
        'thread_id': '0x7d1',
        'pid': 24,
        'euid': 0,
        'library': '/System/Library/PrivateFrameworks/SkyLight.framework/Versions/A/SkyLight',
        'library_uuid': 'C0FDF86CF96037A3A380DB8700D43801',
        'boot_uuid': 'DCA6F38213F54A21BF2B4F1BE8B136BD',
        'process': '/usr/libexec/UserEventAgent',
        'process_uuid': '36B63A883FE730FCB7BA46C45DD6B7D8',
        'message': 'Failed to look up the port for "com.apple.windowserver.active" (1102)'
        }

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
    self.CheckEventData(event_data, expected_event_values)

  def testPersistParsing(self):
    """Tests the Parse function on a Persist tracev3."""
    parser = aul.AULParser()
    storage_writer = self._ParseFile([
      'AUL', 'private', 'var', 'db', 'Diagnostics', 'Persist',
      '0000000000000001.tracev3'
    ], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event_data')
    self.assertEqual(number_of_events, 82995)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'mac:aul:event',
        'creation_time': '2023-01-12T01:35:35.240424704+00:00',
        'level': 'Default',
        'thread_id': '0x0',
        'pid': 0,
        'euid': 0,
        'library': '/kernel',
        'library_uuid': 'D1CD0AAF523E312F92996116B1D511FE',
        'boot_uuid': 'DCA6F38213F54A21BF2B4F1BE8B136BD',
        'process': '/kernel',
        'process_uuid': 'D1CD0AAF523E312F92996116B1D511FE',
        'message': 'initialize_screen: b=BE3A18000, w=00000280, h=00000470, r=00000A00, d=00000000\n'
        }

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 22)
    self.CheckEventData(event_data, expected_event_values)

if __name__ == '__main__':
  unittest.main()
