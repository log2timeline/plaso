#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the PE file parser."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import artifacts
from plaso.lib import definitions
from plaso.parsers import pe

from tests.parsers import test_lib


class PECOFFTest(test_lib.ParserTestCase):
  """Tests for the PE file parser."""

  # pylint: disable=protected-access

  def testParseFileObjectOnExecutable(self):
    """Tests the ParseFileObject on a PE executable (EXE) file."""
    parser = pe.PEParser()
    storage_writer = self._ParseFile(['test_pe.exe'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'pe',
        'date_time': '2015-04-21 14:53:56',
        'pe_attribute': None,
        'pe_type': 'Executable (EXE)',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'data_type': 'pe',
        'date_time': '2015-04-21 14:53:55',
        'pe_attribute': 'DIRECTORY_ENTRY_IMPORT',
        'pe_type': 'Executable (EXE)',
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'data_type': 'pe',
        'date_time': '2015-04-21 14:53:54',
        'dll_name': 'USER32.dll',
        'imphash': '8d0739063fc8f9955cc6696b462544ab',
        'pe_attribute': 'DIRECTORY_ENTRY_DELAY_IMPORT',
        'pe_type': 'Executable (EXE)',
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

  def testParseFileObjectOnDriver(self):
    """Tests the ParseFileObject on a PE driver (SYS) file."""
    parser = pe.PEParser()
    storage_writer = self._ParseFile(['test_driver.sys'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'pe',
        'date_time': '2015-04-21 14:53:54',
        'pe_attribute': None,
        'pe_type': 'Driver (SYS)',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

  def testParseFileObjectOnResourceFile(self):
    """Tests the ParseFileObject on a resource Dynamic Link Library file."""
    test_file_path = self._GetTestFilePath(['wrc-test-wevt_template.dll'])
    self._SkipIfPathNotExists(test_file_path)

    test_event_provider = artifacts.WindowsEventLogMessageFileArtifact()

    parser = pe.PEParser()

    storage_writer = self._CreateStorageWriter()

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)

    parser_mediator = self._CreateParserMediator(
        storage_writer, file_entry=file_entry)
    parser_mediator._extract_winevt_resources = True
    parser_mediator._windows_event_log_providers_per_path = {
        os.path.dirname(test_file_path).lower(): {
            'wrc-test-wevt_template.dll': test_event_provider}}

    file_object = file_entry.GetFileObject()
    parser.Parse(parser_mediator, file_object)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'pe',
        'date_time': '2022-01-03 08:55:07',
        'pe_attribute': None,
        'pe_type': 'Dynamic Link Library (DLL)',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'windows_eventlog_message_string')
    self.assertEqual(number_of_artifacts, 1)

    attribute_containers = list(storage_writer.GetAttributeContainers(
        'windows_eventlog_message_string'))
    self.assertEqual(attribute_containers[0].message_identifier, 0xb0010001)
    self.assertEqual(attribute_containers[0].language_identifier, 1033)
    self.assertEqual(attribute_containers[0].string, 'A test value')

    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'windows_wevt_template_event')
    self.assertEqual(number_of_artifacts, 1)

    attribute_containers = list(storage_writer.GetAttributeContainers(
        'windows_wevt_template_event'))
    self.assertEqual(attribute_containers[0].identifier, 1)
    self.assertEqual(attribute_containers[0].message_identifier, 0xb0010001)
    self.assertEqual(
        attribute_containers[0].provider_identifier,
        '{67883bbc-d592-4d02-8e29-66907fcb07d6}')
    self.assertIsNone(attribute_containers[0].version)


if __name__ == '__main__':
  unittest.main()
