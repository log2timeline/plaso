#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Apple Unified Logging (AUL) tracev3 file parser."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.parsers import unified_logging

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class UnifiedLoggingParserTest(test_lib.ParserTestCase):
  """Tests for the Apple Unified Logging (AUL) tracev3 file parser."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    test_file_path = os.path.join(
        shared_test_lib.TEST_DATA_PATH, 'unified_logging1.dmg')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_MODI, parent=test_path_spec)
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GPT, location='/p1',
        parent=test_path_spec)
    self._parent_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS_CONTAINER,
        parent=test_path_spec, volume_index=0)

  def testSpecialParsing(self):
    """Tests the Parse function on a Special tracev3 file."""
    test_file_path = (
        '/private/var/db/Diagnostics/Special/0000000000000001.tracev3')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_file_path,
        parent=self._parent_path_spec)

    parser = unified_logging.UnifiedLoggingParser()
    storage_writer = self._ParseFileByPathSpec(test_path_spec, parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    # self.assertEqual(number_of_events, 12154)
    self.assertEqual(number_of_events, 12134)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'body': (
            'Failed to look up the port for "com.apple.windowserver.active" '
            '(1102)'),
        'boot_uuid': 'DCA6F382-13F5-4A21-BF2B-4F1BE8B136BD',
        # 'creation_time': '2023-01-12T01:36:27.111432704+00:00',
        'creation_time': '2023-01-12T01:36:27.098762953+00:00',
        'data_type': 'macos:unified_logging:event',
        # 'euid': 0,
        # 'level': 'Default',
        'library': (
            '/System/Library/PrivateFrameworks/'
            'SkyLight.framework/Versions/A/SkyLight'),
        'library_uuid': 'C0FDF86C-F960-37A3-A380-DB8700D43801',
        'pid': 24,
        'process': '/usr/libexec/UserEventAgent',
        'process_uuid': '36B63A88-3FE7-30FC-B7BA-46C45DD6B7D8',
        'subsystem': 'com.apple.SkyLight',
        'thread_identifier': 0x7d1}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
    self.CheckEventData(event_data, expected_event_values)

  @unittest.skip('slow test: 113.768s')
  def testPersistParsing(self):
    """Tests the Parse function on a Persist tracev3 file."""
    test_file_path = (
        '/private/var/db/Diagnostics/Persist/0000000000000001.tracev3')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_file_path,
        parent=self._parent_path_spec)

    parser = unified_logging.UnifiedLoggingParser()
    storage_writer = self._ParseFileByPathSpec(test_path_spec, parser)

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
        'body': (
            'initialize_screen: b=BE3A18000, w=00000280, h=00000470, '
            'r=00000A00, d=00000000\n'),
        'boot_uuid': 'DCA6F382-13F5-4A21-BF2B-4F1BE8B136BD',
        'creation_time': '2023-01-12T01:35:35.240424704+00:00',
        'data_type': 'macos:unified_logging:event',
        # 'euid': 0,
        # 'level': 'Default',
        'library': '/kernel',
        'library_uuid': 'D1CD0AAF523E312F92996116B1D511FE',
        'pid': 0,
        'process': '/kernel',
        'process_uuid': 'D1CD0AAF523E312F92996116B1D511FE',
        'thread_identifier': 0}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 22)
    self.CheckEventData(event_data, expected_event_values)

  def testSignpostParsing(self):
    """Tests the Parse function on a Signpost tracev3 file."""
    test_file_path = (
        '/private/var/db/Diagnostics/Signpost/0000000000000001.tracev3')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_file_path,
        parent=self._parent_path_spec)

    parser = unified_logging.UnifiedLoggingParser()
    storage_writer = self._ParseFileByPathSpec(test_path_spec, parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_events, 2461)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # TODO: 'Signpost ID: EEEEB0B5B2B2EEEE - Signpost Name: 1D4930'
    expected_event_values = {
        'body': (
            'Kext com.apple.driver.KextExcludeList v17.0.0 in codeless kext '
            'bundle com.apple.driver.KextExcludeList at /Library/Apple/System/'
            'Library/Extensions/AppleKextExcludeList.kext: FS contents are '
            'valid'),
        'boot_uuid': 'DCA6F382-13F5-4A21-BF2B-4F1BE8B136BD',
        'category': 'Speed',
        # 'creation_time': '2023-01-12T01:36:31.338352128+00:00',
        'creation_time': '2023-01-12T01:36:31.258051782+00:00',
        'data_type': 'macos:unified_logging:event',
        # 'euid': 0,
        # 'level': 'Signpost',
        'library': '/usr/libexec/kernelmanagerd',
        'library_uuid': '5FCEBDDD-0174-3777-BB92-E98174383008',
        'pid': 50,
        'process': '/usr/libexec/kernelmanagerd',
        'process_uuid': '5FCEBDDD-0174-3777-BB92-E98174383008',
        'thread_identifier': 0x7cb}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
