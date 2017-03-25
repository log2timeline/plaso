#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Systemd Journal parser."""

try:
  import lzma
except ImportError:
  lzma = None

import unittest

from plaso.lib import errors
from plaso.lib import timelib
from plaso.parsers import systemd_journal

from tests.parsers import test_lib


@unittest.skipUnless(lzma, 'lzma missing')
class SystemdJournalParserTest(test_lib.ParserTestCase):
  """Tests for the Systemd Journal parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = systemd_journal.SystemdJournalParser()
    journal = self._ParseFile([
        u'systemd', u'journal', u'system.journal'], parser)

    self.assertEqual(len(journal.events), 2101)

    event = journal.events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2017-01-27 09:40:55.913258')

    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'test-VirtualBox [systemd, pid: 1] Started User Manager for '
        u'UID 1000.')
    self._TestGetMessageStrings(event, expected_message, expected_message)

    # This event uses XZ compressed data
    event = journal.events[2098]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2017-02-06 16:24:32.564585')

    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = u'test-VirtualBox [root, pid: 22921] {0:s}'.format(
        u'a' * 692)
    expected_short_message = u'{0:s}...'.format(expected_message[:77])
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

  def testParseDirty(self):
    """Tests the Parse function on a 'dirty' journal file."""
    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)
    parser = systemd_journal.SystemdJournalParser()
    path_segments = [
        u'systemd', u'journal',
        u'system@00053f9c9a4c1e0e-2e18a70e8b327fed.journalTILDE'
    ]
    file_entry = self._GetTestFileEntry(path_segments)
    file_object = file_entry.GetFileObject()

    with self.assertRaisesRegexp(
        errors.ParseError,
        ur'object offset should be after hash tables \([0-9]+ < [0-9]+\)'):
      parser.ParseFileObject(parser_mediator, file_object)

    self.assertEqual(len(storage_writer.events), 2211)

    event = storage_writer.events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-10-24 13:20:01.063423')

    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'test-VirtualBox [systemd-journald, pid: 569] Runtime journal '
        u'(/run/log/journal/) is 1.2M, max 9.9M, 8.6M free.')
    expected_short_message = u'{0:s}...'.format(expected_message[:77])
    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
