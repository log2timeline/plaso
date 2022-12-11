#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Systemd Journal parser."""

import unittest

from plaso.containers import warnings
from plaso.parsers import systemd_journal

from tests.parsers import test_lib


class SystemdJournalParserTest(test_lib.ParserTestCase):
  """Tests for the Systemd Journal parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = systemd_journal.SystemdJournalParser()
    storage_writer = self._ParseFile([
        'systemd', 'journal', 'system.journal'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2101)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'body': 'Started User Manager for UID 1000.',
        'data_type': 'systemd:journal',
        'hostname': 'test-VirtualBox',
        'pid': '1',
        'reporter': 'systemd',
        'written_time': '2017-01-27T09:40:55.913258+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Test a XZ compressed data log entry.
    expected_event_values = {
        'body': 'a' * 692,
        'data_type': 'systemd:journal',
        'hostname': 'test-VirtualBox',
        'pid': '22921',
        'reporter': 'root',
        'written_time': '2017-02-06T16:24:32.564585+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2098)
    self.CheckEventData(event_data, expected_event_values)

  def testParseLZ4(self):
    """Tests the Parse function on a journal with LZ4 compressed events."""
    parser = systemd_journal.SystemdJournalParser()
    storage_writer = self._ParseFile([
        'systemd', 'journal', 'system.journal.lz4'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 85)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'body': 'Reached target Paths.',
        'data_type': 'systemd:journal',
        'hostname': 'testlol',
        'pid': '822',
        'reporter': 'systemd',
        'written_time': '2018-07-03T15:00:16.682340+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Test a LZ4 compressed data log entry.
    # The text used in the test message was triplicated to make it long enough
    # to trigger the LZ4 compression.
    # Source: https://github.com/systemd/systemd/issues/6237
    expected_body_parts = [' textual user names.']
    expected_body_parts.extend(
        ('  Yes, as you found out 0day is not a valid username. I wonder which '
         'tool permitted you to create it in the first place. Note that not '
         'permitting numeric first characters is done on purpose: to avoid '
         'ambiguities between numeric UID and textual user names.') * 3)
    expected_body = ''.join(expected_body_parts)

    expected_event_values = {
        'body': expected_body,
        'data_type': 'systemd:journal',
        'hostname': 'testlol',
        'pid': '34757',
        'reporter': 'test',
        'written_time': '2018-07-03T15:19:04.667807+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 84)
    self.CheckEventData(event_data, expected_event_values)

  def testParseDirty(self):
    """Tests the Parse function on a 'dirty' journal file."""
    parser = systemd_journal.SystemdJournalParser()

    storage_writer = self._ParseFile([
        'systemd', 'journal',
        'system@00053f9c9a4c1e0e-2e18a70e8b327fed.journalTILDE'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2211)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'body': ('Runtime journal (/run/log/journal/) is 1.2M, max 9.9M, 8.6M '
                 'free.'),
        'data_type': 'systemd:journal',
        'hostname': 'test-VirtualBox',
        'pid': '569',
        'reporter': 'systemd-journald',
        'written_time': '2016-10-24T13:20:01.063423+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    generator = storage_writer.GetAttributeContainers(
        warnings.ExtractionWarning.CONTAINER_TYPE)

    test_warnings = list(generator)
    test_warning = test_warnings[0]
    self.assertIsNotNone(test_warning)

    expected_message = (
        'Unable to parse journal entry at offset: 0x0041bfb0 with error: '
        'object offset should be after hash tables (0 < 2527472)')
    self.assertEqual(test_warning.message, expected_message)


if __name__ == '__main__':
  unittest.main()
