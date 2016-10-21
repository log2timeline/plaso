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
    journal = self._ParseFile([u'systemd', u'system.journal'], parser_object)

    self.assertEqual(
        len(journal.events), parser_object.journal_header.n_entries)

    event_object = journal.events[0]
    print event_object
    expected_dict = {
        u'DISK_AVAILABLE':
            u'206946304',
        u'DISK_AVAILABLE_PRETTY':
            u'197.3M',
        u'_BOOT_ID':
            u'a2005bac13054a889146a742c2eeaa6e',
        u'CURRENT_USE':
            u'2625536',
        u'LIMIT':
            u'20979712',
        u'_GID':
            u'0',
        u'AVAILABLE_PRETTY':
            u'17.5M',
        u'AVAILABLE':
            u'18354176',
        u'PRIORITY':
            u'6',
        u'_TRANSPORT':
            u'driver',
        u'_HOSTNAME':
            u'test-VirtualBox',
        u'DISK_KEEP_FREE':
            u'31465472',
        u'MAX_USE_PRETTY':
            u'20.0M',
        u'CURRENT_USE_PRETTY':
            u'2.5M',
        u'DISK_KEEP_FREE_PRETTY':
            u'30.0M',
        u'_CAP_EFFECTIVE':
            u'25402800cf',
        u'_SYSTEMD_UNIT':
            u'systemd-journald.service',
        u'_MACHINE_ID':
            u'a447b9eff9fe40a890e8e376e92a4ede',
        u'_PID':
            u'588',
        u'SYSLOG_IDENTIFIER':
            u'systemd-journald',
        u'_SYSTEMD_CGROUP':
            u'/system.slice/systemd-journald.service',
        u'MAX_USE':
            u'20979712',
        u'JOURNAL_NAME':
            u'Runtime journal',
        u'MESSAGE_ID':
            u'ec387f577b844b8fa948f33cad9a75e6',
        u'_COMM':
            u'systemd-journal',
        u'LIMIT_PRETTY':
            u'20.0M',
        u'JOURNAL_PATH':
            u'/run/log/journal/',
        u'_CMDLINE':
            u'/lib/systemd/systemd-journald',
        u'_SYSTEMD_SLICE':
            u'system.slice',
        u'_EXE':
            u'/lib/systemd/systemd-journald',
        u'_UID':
            u'0',
        u'MESSAGE':
            u'Runtime journal (/run/log/journal/) is 2.5M, max 20.0M, 17.5M free.'
    }

    self.assertEqual(event_object.raw_dict, expected_dict)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-07-27 06:41:47')
    #self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_msg="msg"
    expected_msg_short="msg_short"
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
