#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Apple Unified Logging (AUL) parser."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.parsers import unified_logging

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class AULParserTest(test_lib.ParserTestCase):
  """Tests for the AUL parser."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    aul_test_data = os.path.join(
        shared_test_lib.TEST_DATA_PATH, 'AUL', 'aul_test_data.zip')
    self._zip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=aul_test_data)

  def testSpecialParsing(self):
    """Tests the Parse function on a Special tracev3."""
    test_file = os.path.join(
        '/', 'private', 'var', 'db', 'Diagnostics', 'Special',
        '0000000000000001.tracev3')
    zip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_ZIP, location=test_file,
        parent=self._zip_path_spec)

    parser = unified_logging.AULParser()
    storage_writer = self._ParseFileByPathSpec(zip_path_spec, parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_events, 12154)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'macos:unified_logging:event',
        'creation_time': '2023-01-12T01:36:27.111432704+00:00',
        'level': 'Default',
        'subsystem': 'com.apple.SkyLight',
        'thread_identifier': 0x7d1,
        'pid': 24,
        'euid': 0,
        'library': ('/System/Library/PrivateFrameworks/'
            'SkyLight.framework/Versions/A/SkyLight'),
        'library_uuid': 'C0FDF86CF96037A3A380DB8700D43801',
        'boot_uuid': 'DCA6F38213F54A21BF2B4F1BE8B136BD',
        'process': '/usr/libexec/UserEventAgent',
        'process_uuid': '36B63A883FE730FCB7BA46C45DD6B7D8',
        'body': ('Failed to look up the port for '
            '"com.apple.windowserver.active" (1102)')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
    self.CheckEventData(event_data, expected_event_values)

  def testPersistParsing(self):
    """Tests the Parse function on a Persist tracev3."""
    parser = unified_logging.AULParser()
    storage_writer = self._ParseFile([
        'AUL', 'private', 'var', 'db', 'Diagnostics', 'Persist',
        '0000000000000001.tracev3'
    ], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_events, 82995)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'macos:unified_logging:event',
        'creation_time': '2023-01-12T01:35:35.240424704+00:00',
        'level': 'Default',
        'thread_identifier': 0,
        'pid': 0,
        'euid': 0,
        'library': '/kernel',
        'library_uuid': 'D1CD0AAF523E312F92996116B1D511FE',
        'boot_uuid': 'DCA6F38213F54A21BF2B4F1BE8B136BD',
        'process': '/kernel',
        'process_uuid': 'D1CD0AAF523E312F92996116B1D511FE',
        'body': ('initialize_screen: b=BE3A18000, w=00000280, h=00000470, '
            'r=00000A00, d=00000000\n')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 22)
    self.CheckEventData(event_data, expected_event_values)

  def testSignpostParsing(self):
    """Tests the Parse function on a Signpost tracev3."""
    parser = unified_logging.AULParser()
    storage_writer = self._ParseFile([
        'AUL', 'private', 'var', 'db', 'Diagnostics', 'Signpost',
        '0000000000000001.tracev3'
    ], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_events, 2461)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'macos:unified_logging:event',
        'creation_time': '2023-01-12T01:36:31.338352128+00:00',
        'level': 'Signpost',
        'thread_identifier': 0x7cb,
        'pid': 50,
        'euid': 0,
        'library': '/usr/libexec/kernelmanagerd',
        'library_uuid': '5FCEBDDD01743777BB92E98174383008',
        'boot_uuid': 'DCA6F38213F54A21BF2B4F1BE8B136BD',
        'process': '/usr/libexec/kernelmanagerd',
        'process_uuid': '5FCEBDDD01743777BB92E98174383008',
        'category': 'Speed',
        'body': ('Signpost ID: EEEEB0B5B2B2EEEE - Signpost Name: 1D4930 '
            '- Kext com.apple.driver.KextExcludeList v17.0.0 in '
            'codeless kext bundle com.apple.driver.KextExcludeList at '
            '/Library/Apple/System/Library/Extensions/'
            'AppleKextExcludeList.kext: FS contents are valid')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
