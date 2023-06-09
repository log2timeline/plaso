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

  @unittest.skip('slow test: 113.768s')
  def testParseWithPersistTraceV3(self):
    """Tests the Parse function with a Persist tracev3 file."""
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
        'activity_identifier': 0,
        'boot_identifier': 'DCA6F382-13F5-4A21-BF2B-4F1BE8B136BD',
        'data_type': 'macos:unified_logging:event',
        # 'euid': 0,
        'event_message': (
            'initialize_screen: b=BE3A18000, w=00000280, h=00000470, '
            'r=00000A00, d=00000000\n'),
        'event_type': 'logEvent',
        'message_type': 'Default',
        'pid': 0,
        'process_image_identifier': 'D1CD0AAF-523E-312F-9299-6116B1D511FE',
        'process_image_path': '/kernel',
        'recorded_time': '2023-01-12T01:35:35.240424704+00:00',
        'sender_image_identifier': 'D1CD0AAF-523E-312F-9299-6116B1D511FE',
        'sender_image_path': '/kernel',
        'thread_identifier': 0}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 22)
    self.CheckEventData(event_data, expected_event_values)

  def testParseWithSignpostTraceV3(self):
    """Tests the Parse function with a Signpost tracev3 file."""
    test_file_path = (
        '/private/var/db/Diagnostics/Signpost/0000000000000001.tracev3')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_file_path,
        parent=self._parent_path_spec)

    parser = unified_logging.UnifiedLoggingParser()
    storage_writer = self._ParseFileByPathSpec(test_path_spec, parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_events, 2466)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'activity_identifier': 0,
        'boot_identifier': 'DCA6F382-13F5-4A21-BF2B-4F1BE8B136BD',
        'category': 'Speed',
        'data_type': 'macos:unified_logging:event',
        # 'euid': 0,
        'event_message': (
            'Kext com.apple.driver.KextExcludeList v17.0.0 in codeless kext '
            'bundle com.apple.driver.KextExcludeList at /Library/Apple/System/'
            'Library/Extensions/AppleKextExcludeList.kext: FS contents are '
            'valid'),
        'event_type': 'signpostEvent',
        'message_type': None,
        'pid': 50,
        'process_image_identifier': '5FCEBDDD-0174-3777-BB92-E98174383008',
        'process_image_path': '/usr/libexec/kernelmanagerd',
        # 'recorded_time': '2023-01-12T01:36:31.338352128+00:00',
        'recorded_time': '2023-01-12T01:36:31.338352250+00:00',
        'sender_image_identifier': '5FCEBDDD-0174-3777-BB92-E98174383008',
        'sender_image_path': '/usr/libexec/kernelmanagerd',
        'signpost_identifier': 0xeeeeb0b5b2b2eeee,
        'signpost_name': 'validateExtFilesystem(into:)',
        'thread_identifier': 0x7cb}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 7)
    self.CheckEventData(event_data, expected_event_values)

  def testParseWithSpecialTraceV3(self):
    """Tests the Parse function with a Special tracev3 file."""
    test_file_path = (
        '/private/var/db/Diagnostics/Special/0000000000000001.tracev3')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_file_path,
        parent=self._parent_path_spec)

    parser = unified_logging.UnifiedLoggingParser()
    storage_writer = self._ParseFileByPathSpec(test_path_spec, parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_events, 12159)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'activity_identifier': 0,
        'boot_identifier': 'DCA6F382-13F5-4A21-BF2B-4F1BE8B136BD',
        'data_type': 'macos:unified_logging:event',
        # 'euid': 0,
        'event_message': (
            'Failed to look up the port for "com.apple.windowserver.active" '
            '(1102)'),
        'event_type': 'logEvent',
        'message_type': 'Default',
        'pid': 24,
        'process_image_identifier': '36B63A88-3FE7-30FC-B7BA-46C45DD6B7D8',
        'process_image_path': '/usr/libexec/UserEventAgent',
        # 'recorded_time': '2023-01-12T01:36:27.111432704+00:00',
        'recorded_time': '2023-01-12T01:36:27.111432708+00:00',
        'sender_image_identifier': 'C0FDF86C-F960-37A3-A380-DB8700D43801',
        'sender_image_path': (
            '/System/Library/PrivateFrameworks/'
            'SkyLight.framework/Versions/A/SkyLight'),
        'subsystem': 'com.apple.SkyLight',
        'thread_identifier': 0x7d1}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 8)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
