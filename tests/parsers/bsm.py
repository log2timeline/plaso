#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Basic Security Module (BSM) file parser."""

import unittest

from plaso.formatters import bsm  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import bsm

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class MacOSXBSMParserTest(test_lib.ParserTestCase):
  """Tests for Basic Security Module (BSM) file parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'apple.bsm'])
  def testParse(self):
    """Tests the Parse function on a Mac OS X BSM file."""
    parser = bsm.BSMParser()
    knowledge_base_values = {u'guessed_os': u'MacOSX'}
    storage_writer = self._ParseFile(
        [u'apple.bsm'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 54)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.assertEqual(event.data_type, u'mac:bsm:event')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-04 18:36:20.000381')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(event.event_type, u'audit crash recovery (45029)')

    expected_extra_tokens = {
        u'BSM_TOKEN_PATH': u'/var/audit/20131104171720.crash_recovery',
        u'BSM_TOKEN_RETURN32': {
            u'call_status': 0,
            u'error': u'Success',
            u'token_status': 0},
        u'BSM_TOKEN_TEXT': u'launchctl::Audit recovery',
        u'BSM_TOKEN_TRAILER': 104
    }

    self.assertEqual(event.extra_tokens, expected_extra_tokens)

    expected_return_value = {
        u'call_status': 0,
        u'error': u'Success',
        u'token_status': 0
    }
    self.assertEqual(event.return_value, expected_return_value)

    event = events[15]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-04 18:36:26.000171')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(event.event_type, u'user authentication (45023)')

    expected_extra_tokens = {
        u'BSM_TOKEN_RETURN32': {
            u'call_status': 5000,
            u'error': u'Unknown',
            u'token_status': 255},

        u'BSM_TOKEN_SUBJECT32': {
            u'aid': 4294967295,
            u'egid': 92,
            u'euid': 92,
            u'gid': 92,
            u'pid': 143,
            u'session_id': 100004,
            u'terminal_ip': '0.0.0.0',
            u'terminal_port': 143,
            u'uid': 92},

        u'BSM_TOKEN_TEXT': (u'Verify password for record type Users '
                            u'\'moxilo\' node \'/Local/Default\''),

        u'BSM_TOKEN_TRAILER': 140
    }

    self.assertEqual(event.extra_tokens, expected_extra_tokens)

    expected_return_value = {
        u'call_status': 5000,
        u'error': u'Unknown',
        u'token_status': 255
    }
    self.assertEqual(event.return_value, expected_return_value)

    event = events[31]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-04 18:36:26.000530')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.event_type, u'SecSrvr AuthEngine (45025)')
    expected_extra_tokens = {
        u'BSM_TOKEN_RETURN32': {
            u'call_status': 0,
            u'error': u'Success',
            u'token_status': 0},
        u'BSM_TOKEN_SUBJECT32': {
            u'aid': 4294967295,
            u'egid': 0,
            u'euid': 0,
            u'gid': 0,
            u'pid': 67,
            u'session_id': 100004,
            u'terminal_ip': '0.0.0.0',
            u'terminal_port': 67,
            u'uid': 0},
        u'BSM_TOKEN_TEXT': u'system.login.done',
        u'BSM_TOKEN_TRAILER': 110
    }
    self.assertEqual(event.extra_tokens, expected_extra_tokens)

    expected_return_value = {
        u'call_status': 0,
        u'error': u'Success',
        u'token_status': 0
    }
    self.assertEqual(event.return_value, expected_return_value)

    event = events[50]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-04 18:37:36.000399')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.event_type, u'session end (44903)')

    expected_extra_tokens = {
        u'BSM_TOKEN_ARGUMENT32': {
            u'is': 12288,
            u'num_arg': 3,
            u'string': u'am_failure'},
        u'BSM_TOKEN_ARGUMENT64': {
            u'is': 0,
            u'num_arg': 1,
            u'string': u'sflags'},
        u'BSM_TOKEN_RETURN32': {
            u'call_status': 0,
            u'error': u'Success',
            u'token_status': 0},
        u'BSM_TOKEN_SUBJECT32': {
            u'aid': 4294967295,
            u'egid': 0,
            u'euid': 0,
            u'gid': 0,
            u'pid': 0,
            u'session_id': 100015,
            u'terminal_ip': '0.0.0.0',
            u'terminal_port': 0,
            u'uid': 0},
        u'BSM_TOKEN_TRAILER': 125
    }
    self.assertEqual(event.extra_tokens, expected_extra_tokens)

    expected_return_value = {
        u'call_status': 0,
        u'error': u'Success',
        u'token_status': 0
    }
    self.assertEqual(event.return_value, expected_return_value)


class OpenBSMParserTest(test_lib.ParserTestCase):
  """Tests for Basic Security Module (BSM) file parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'openbsm.bsm'])
  def testParse(self):
    """Tests the Parse function on a "generic" BSM file."""
    parser = bsm.BSMParser()
    knowledge_base_values = {u'guessed_os': u'openbsm'}
    storage_writer = self._ParseFile(
        [u'openbsm.bsm'],
        parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 50)

    events = list(storage_writer.GetEvents())

    expected_extra_tokens = [
        {u'BSM_TOKEN_ARGUMENT32': {
            u'is': 2882400000,
            u'num_arg': 3,
            u'string': u'test_arg32_token'},
         u'BSM_TOKEN_TRAILER': 50},
        {u'BSM_TOKEN_DATA':{
            u'data': u'SomeData',
            u'format': u'String'},
         u'BSM_TOKEN_TRAILER': 39},
        {u'BSM_TOKEN_FILE': {
            u'string': u'test',
            u'timestamp': '1970-01-01 20:42:45'},
         u'BSM_TOKEN_TRAILER': 41},
        {u'BSM_TOKEN_ADDR': '192.168.100.15',
         u'BSM_TOKEN_TRAILER': 30},
        {u'BSM_TOKEN_TRAILER': 46,
         u'IPv4_Header': u'0x400000145478000040010000c0a8649bc0a86e30]'},
        {u'BSM_TOKEN_IPC': {
            u'object_id': 305419896,
            u'object_type': 1},
         u'BSM_TOKEN_TRAILER': 31},
        {u'BSM_TOKEN_PORT': 20480,
         u'BSM_TOKEN_TRAILER': 28},
        {u'BSM_TOKEN_OPAQUE': u'aabbccdd',
         u'BSM_TOKEN_TRAILER': 32},
        {u'BSM_TOKEN_PATH': u'/test/this/is/a/test',
         u'BSM_TOKEN_TRAILER': 49},
        {u'BSM_TOKEN_PROCESS32': {
            u'aid': 305419896,
            u'egid': 591751049,
            u'euid': 19088743,
            u'gid': 159868227,
            u'pid': 321140038,
            u'session_id': 2542171492,
            u'terminal_ip': '127.0.0.1',
            u'terminal_port': 374945606,
            u'uid': 2557891634},
         u'BSM_TOKEN_TRAILER': 62},
        {u'BSM_TOKEN_PROCESS64': {
            u'aid': 305419896,
            u'egid': 591751049,
            u'euid': 19088743,
            u'gid': 159868227,
            u'pid': 321140038,
            u'session_id': 2542171492,
            u'terminal_ip': '127.0.0.1',
            u'terminal_port': 374945606,
            u'uid': 2557891634},
         u'BSM_TOKEN_TRAILER': 66},
        {u'BSM_TOKEN_RETURN32': {
            u'call_status': 305419896,
            u'error': u'Invalid argument',
            u'token_status': 22},
         u'BSM_TOKEN_TRAILER': 31},
        {u'BSM_TOKEN_SEQUENCE': 305419896,
         u'BSM_TOKEN_TRAILER': 30},
        {u'BSM_TOKEN_AUT_SOCKINET32_EX':{
            u'from': '127.0.0.1',
            u'from_port': 0,
            u'to': '127.0.0.1',
            u'to_port': 0},
         u'BSM_TOKEN_TRAILER': 44},
        {u'BSM_TOKEN_SUBJECT32': {
            u'aid': 305419896,
            u'egid': 591751049,
            u'euid': 19088743,
            u'gid': 159868227,
            u'pid': 321140038,
            u'session_id': 2542171492,
            u'terminal_ip': '127.0.0.1',
            u'terminal_port': 374945606,
            u'uid': 2557891634},
         u'BSM_TOKEN_TRAILER': 62},
        {u'BSM_TOKEN_SUBJECT32_EX': {
            u'aid': 305419896,
            u'egid': 591751049,
            u'euid': 19088743,
            u'gid': 159868227,
            u'pid': 321140038,
            u'session_id': 2542171492,
            u'terminal_ip': 'fe80::1',
            u'terminal_port': 374945606,
            u'uid': 2557891634},
         u'BSM_TOKEN_TRAILER': 78},
        {u'BSM_TOKEN_TEXT': u'This is a test.',
         u'BSM_TOKEN_TRAILER': 44},
        {u'BSM_TOKEN_TRAILER': 37,
         u'BSM_TOKEN_ZONENAME': u'testzone'},
        {u'BSM_TOKEN_RETURN32': {
            u'call_status': 4294967295,
            u'error':
            u'Argument list too long',
            u'token_status': 7},
         u'BSM_TOKEN_TRAILER': 31}
    ]

    for event_index in range(0, 19):
      event = events[event_index]
      expected_extra_tokens_dict = expected_extra_tokens[event_index]
      extra_tokens_dict = getattr(event, u'extra_tokens', {})
      self.assertDictContains(extra_tokens_dict, expected_extra_tokens_dict)


if __name__ == '__main__':
  unittest.main()
