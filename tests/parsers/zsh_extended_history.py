#!/usr/bin/python
# -*_ coding: utf-8 -*-
"""Tests for the Zsh extended_history parser."""
import unittest

from plaso.lib import timelib
from plaso.parsers import zsh_extended_history

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class ZshExtendedHistoryTest(test_lib.ParserTestCase):
  """Tests for the Zsh extended_history parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'zsh_extended_history.txt'])
  def testParse(self):
    """Tests for the Parse method."""
    parser_object = zsh_extended_history.ZshExtendedHistoryParser()
    storage_writer = self._ParseFile(
        [u'zsh_extended_history.txt'], parser_object)

    self.assertEqual(len(storage_writer.events), 4)

    event = storage_writer.events[0]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-03-12 08:26:50')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(event.elapsed_seconds, 0)
    self.assertEqual(event.command, u'cd plaso')

    event = storage_writer.events[2]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-03-26 11:54:53')
    expected_command = u'echo dfgdfg \\\\\n& touch /tmp/afile'
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(event.command, expected_command)

    event = storage_writer.events[3]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-03-26 11:54:57')
    self.assertEqual(event.timestamp, expected_timestamp)

  def testVerification(self):
    """Tests for the VerifyStructure method"""
    parser_object = zsh_extended_history.ZshExtendedHistoryParser()

    mediator = None
    valid_lines = u': 1457771210:0;cd plaso'
    self.assertTrue(parser_object.VerifyStructure(mediator, valid_lines))

    invalid_lines = u': 2016-03-26 11:54:53;0;cd plaso'
    self.assertFalse(parser_object.VerifyStructure(mediator, invalid_lines))


if __name__ == '__main__':
  unittest.main()
