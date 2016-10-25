#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Systemd Journal parser."""

import unittest

from plaso.lib import timelib
from plaso.parsers import systemd_journal

from tests.parsers import test_lib

class SystemdJournalParserTest(test_lib.ParserTestCase):
  """ Tests for the Systemd Journal parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser_object = systemd_journal.SystemdJournalParser()
    journal = self._ParseFile([u'systemd', u'journal', u'system.journal'],
                              parser_object)

    self.assertEqual(
        len(journal.events), parser_object.journal_header.n_entries)

    event_object = journal.events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-07-27 06:41:47')

    expected_msg = (u'test-VirtualBox systemd-journald[577] Runtime journal '
                    u'(/run/log/journal/) is 1.2M, max 9.9M, 8.6M free.')
    expected_msg_short = (u'test-VirtualBox systemd-journald[577] Runtime '
                          u'journal (/run/log/journal/) is ...')
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

  def testParseDirty(self):
    """Tests the Parse function on a 'dirty' journal file."""
    parser_object = systemd_journal.SystemdJournalParser()
    journal = self._ParseFile([
        u'systemd', u'journal',
        u'system@00053f9c9a4c1e0e-2e18a70e8b327fed.journalTILDE'
    ], parser_object)

    self.assertEqual(
        len(journal.events), 2211)

    event_object = journal.events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-07-27 06:41:47')

    expected_msg = (u'test-VirtualBox systemd-journald[569] Runtime journal '
                    u'(/run/log/journal/) is 1.2M, max 9.9M, 8.6M free.')
    expected_msg_short = (u'test-VirtualBox systemd-journald[569] Runtime '
                          u'journal (/run/log/journal/) is ...')
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
