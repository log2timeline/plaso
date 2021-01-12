#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Systemd Journal parser."""

import unittest

from plaso.parsers import systemd_journal

from tests.parsers import test_lib


class SystemdJournalParserTest(test_lib.ParserTestCase):
  """Tests for the Systemd Journal parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = systemd_journal.SystemdJournalParser()
    storage_writer = self._ParseFile([
        'systemd', 'journal', 'system.journal'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2101)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'body': 'Started User Manager for UID 1000.',
        'data_type': 'systemd:journal',
        'hostname': 'test-VirtualBox',
        'pid': '1',
        'reporter': 'systemd',
        'timestamp': '2017-01-27 09:40:55.913258'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # Test an event with XZ compressed data.
    expected_event_values = {
        'body': 'a' * 692,
        'data_type': 'systemd:journal',
        'hostname': 'test-VirtualBox',
        'pid': '22921',
        'reporter': 'root',
        'timestamp': '2017-02-06 16:24:32.564585'}

    self.CheckEventValues(storage_writer, events[2098], expected_event_values)

  def testParseLZ4(self):
    """Tests the Parse function on a journal with LZ4 compressed events."""
    parser = systemd_journal.SystemdJournalParser()
    storage_writer = self._ParseFile([
        'systemd', 'journal', 'system.journal.lz4'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 85)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'body': 'Reached target Paths.',
        'data_type': 'systemd:journal',
        'hostname': 'testlol',
        'pid': '822',
        'reporter': 'systemd',
        'timestamp': '2018-07-03 15:00:16.682340'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # Test an event with LZ4 compressed data.
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
        'timestamp': '2018-07-03 15:19:04.667807'}

    self.CheckEventValues(storage_writer, events[84], expected_event_values)

  def testParseDirty(self):
    """Tests the Parse function on a 'dirty' journal file."""
    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)
    parser = systemd_journal.SystemdJournalParser()

    path_segments = [
        'systemd', 'journal',
        'system@00053f9c9a4c1e0e-2e18a70e8b327fed.journalTILDE']
    file_entry = self._GetTestFileEntry(path_segments)
    file_object = file_entry.GetFileObject()

    parser.ParseFileObject(parser_mediator, file_object)

    self.assertEqual(storage_writer.number_of_warnings, 1)
    self.assertEqual(storage_writer.number_of_events, 2211)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'body': (
            'Runtime journal (/run/log/journal/) is 1.2M, max 9.9M, 8.6M '
            'free.'),
        'data_type': 'systemd:journal',
        'hostname': 'test-VirtualBox',
        'pid': '569',
        'reporter': 'systemd-journald',
        'timestamp': '2016-10-24 13:20:01.063423'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    warnings = list(storage_writer.GetExtractionWarnings())
    warning = warnings[0]
    expected_warning_message = (
        'Unable to parse journal entry at offset: 0x0041bfb0 with error: '
        'object offset should be after hash tables (0 < 2527472)')
    self.assertEqual(warning.message, expected_warning_message)


if __name__ == '__main__':
  unittest.main()
