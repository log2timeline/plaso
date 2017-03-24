"""Tests for the Systemd Journal parser."""

import unittest

from plaso.lib import errors
from plaso.lib import timelib

from tests.parsers import test_lib


class SystemdJournalParserTest(test_lib.ParserTestCase):
  """Tests for the Systemd Journal parser."""

  # pylint: disable=protected-access
  def testParse(self):
    """Tests the Parse function."""

    try:
      from plaso.parsers import systemd_journal
    except ImportError as e:
      if e.message.find(u'lzma') > 0:
        raise unittest.SkipTest(u'python lzma is not installed')

    parser_object = systemd_journal.SystemdJournalParser()
    journal = self._ParseFile([
        u'systemd', u'journal', u'system.journal'], parser_object)

    self.assertEqual(
        len(journal.events), parser_object._journal_header.n_entries)

    event = journal.events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2017-01-27 09:40:55.913258')

    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'test-VirtualBox systemd[1] Started User Manager for '
        u'UID 1000.')
    self._TestGetMessageStrings(event, expected_message, expected_message)

    # This event uses XZ compressed data
    event = journal.events[2098]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2017-02-06 16:24:32.564585')

    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = u'test-VirtualBox root[22921] {0:s}'.format(u'a'*692)
    expected_message_short = u'test-VirtualBox root[22921] {0:s}...'.format(
        u'a' * 49)
    self._TestGetMessageStrings(event, expected_message, expected_message_short)

  def testParseDirty(self):
    """Tests the Parse function on a 'dirty' journal file."""

    try:
      from plaso.parsers import systemd_journal
    except ImportError as e:
      if e.message.find(u'lzma') > 0:
        raise unittest.SkipTest(u'python lzma is not installed')

    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)
    parser_object = systemd_journal.SystemdJournalParser()
    path_segments = [
        u'systemd', u'journal',
        u'system@00053f9c9a4c1e0e-2e18a70e8b327fed.journalTILDE'
    ]
    file_entry = self._GetTestFileEntry(path_segments)
    file_object = file_entry.GetFileObject()

    with self.assertRaisesRegexp(
        errors.ParseError,
        ur'object offset should be after hash tables \([0-9]+ < [0-9]+\)'):
      parser_object.ParseFileObject(parser_mediator, file_object)

    self.assertEqual(len(storage_writer.events), 2211)

    event = storage_writer.events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-10-24 13:20:01.063423')

    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'test-VirtualBox systemd-journald[569] Runtime journal '
        u'(/run/log/journal/) is 1.2M, max 9.9M, 8.6M free.')
    expected_message_short = (
        u'test-VirtualBox systemd-journald[569] Runtime journal '
        u'(/run/log/journal/) is ...')
    self._TestGetMessageStrings(event, expected_message, expected_message_short)


if __name__ == '__main__':
  unittest.main()
