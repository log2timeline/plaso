#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Systemd Journal parser."""

from __future__ import unicode_literals

import unittest

from plaso.parsers import systemd_journal

from tests.parsers import test_lib


@unittest.skipIf(systemd_journal is None, 'requires LZMA compression support')
class SystemdJournalParserTest(test_lib.ParserTestCase):
  """Tests for the Systemd Journal parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = systemd_journal.SystemdJournalParser()
    storage_writer = self._ParseFile([
        'systemd', 'journal', 'system.journal'], parser)

    self.assertEqual(storage_writer.number_of_events, 2101)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2017-01-27 09:40:55.913258')

    expected_message = (
        'test-VirtualBox [systemd, pid: 1] Started User Manager for '
        'UID 1000.')
    self._TestGetMessageStrings(event, expected_message, expected_message)

    # This event uses XZ compressed data
    event = events[2098]

    self.CheckTimestamp(event.timestamp, '2017-02-06 16:24:32.564585')

    expected_message = 'test-VirtualBox [root, pid: 22921] {0:s}'.format(
        'a' * 692)
    expected_short_message = '{0:s}...'.format(expected_message[:77])
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

  def testParseDirty(self):
    """Tests the Parse function on a 'dirty' journal file."""
    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)
    parser = systemd_journal.SystemdJournalParser()
    path_segments = [
        'systemd', 'journal',
        'system@00053f9c9a4c1e0e-2e18a70e8b327fed.journalTILDE'
    ]
    file_entry = self._GetTestFileEntry(path_segments)
    file_object = file_entry.GetFileObject()

    parser.ParseFileObject(parser_mediator, file_object)

    self.assertEqual(storage_writer.number_of_events, 2211)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2016-10-24 13:20:01.063423')

    expected_message = (
        'test-VirtualBox [systemd-journald, pid: 569] Runtime journal '
        '(/run/log/journal/) is 1.2M, max 9.9M, 8.6M free.')
    expected_short_message = '{0:s}...'.format(expected_message[:77])
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    self.assertEqual(storage_writer.number_of_errors, 1)

    errors = list(storage_writer.GetErrors())
    error = errors[0]
    expected_error_message = (
        'Unable to complete parsing journal file: '
        'object offset should be after hash tables (4308912 < 2527472) at '
        'offset 0x0041bfb0')
    self.assertEqual(error.message, expected_error_message)


if __name__ == '__main__':
  unittest.main()
