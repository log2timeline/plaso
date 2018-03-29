#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for Basic Security Module (BSM) file parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import bsm as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers import bsm

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class MacOSBSMParserTest(test_lib.ParserTestCase):
  """Tests for Basic Security Module (BSM) file parser."""

  @shared_test_lib.skipUnlessHasTestFile(['apple.bsm'])
  def testParse(self):
    """Tests the Parse function on a MacOS BSM file."""
    parser = bsm.BSMParser()
    knowledge_base_values = {
        'operating_system': definitions.OPERATING_SYSTEM_MACOS}
    storage_writer = self._ParseFile(
        ['apple.bsm'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 54)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.assertEqual(event.data_type, 'bsm:event')

    self.CheckTimestamp(event.timestamp, '2013-11-04 18:36:20.000381')

    self.assertEqual(event.event_type, 'audit crash recovery (45029)')

    expected_extra_tokens = {
        'BSM_TOKEN_PATH': '/var/audit/20131104171720.crash_recovery',
        'BSM_TOKEN_RETURN32': {
            'call_status': 0,
            'error': 'Success',
            'token_status': 0},
        'BSM_TOKEN_TEXT': 'launchctl::Audit recovery',
        'BSM_TOKEN_TRAILER': 104
    }

    self.assertEqual(event.extra_tokens, expected_extra_tokens)

    expected_return_value = {
        'call_status': 0,
        'error': 'Success',
        'token_status': 0
    }
    self.assertEqual(event.return_value, expected_return_value)

    event = events[15]

    self.CheckTimestamp(event.timestamp, '2013-11-04 18:36:26.000171')

    self.assertEqual(event.event_type, 'user authentication (45023)')

    expected_extra_tokens = {
        'BSM_TOKEN_RETURN32': {
            'call_status': 5000,
            'error': 'Unknown',
            'token_status': 255},

        'BSM_TOKEN_SUBJECT32': {
            'aid': 4294967295,
            'egid': 92,
            'euid': 92,
            'gid': 92,
            'pid': 143,
            'session_id': 100004,
            'terminal_ip': '0.0.0.0',
            'terminal_port': 143,
            'uid': 92},

        'BSM_TOKEN_TEXT': (
            'Verify password for record type Users \'moxilo\' node '
            '\'/Local/Default\''),

        'BSM_TOKEN_TRAILER': 140
    }

    self.assertEqual(event.extra_tokens, expected_extra_tokens)

    expected_return_value = {
        'call_status': 5000,
        'error': 'Unknown',
        'token_status': 255
    }
    self.assertEqual(event.return_value, expected_return_value)

    event = events[31]

    self.CheckTimestamp(event.timestamp, '2013-11-04 18:36:26.000530')

    self.assertEqual(event.event_type, 'SecSrvr AuthEngine (45025)')
    expected_extra_tokens = {
        'BSM_TOKEN_RETURN32': {
            'call_status': 0,
            'error': 'Success',
            'token_status': 0},
        'BSM_TOKEN_SUBJECT32': {
            'aid': 4294967295,
            'egid': 0,
            'euid': 0,
            'gid': 0,
            'pid': 67,
            'session_id': 100004,
            'terminal_ip': '0.0.0.0',
            'terminal_port': 67,
            'uid': 0},
        'BSM_TOKEN_TEXT': 'system.login.done',
        'BSM_TOKEN_TRAILER': 110
    }
    self.assertEqual(event.extra_tokens, expected_extra_tokens)

    expected_return_value = {
        'call_status': 0,
        'error': 'Success',
        'token_status': 0
    }
    self.assertEqual(event.return_value, expected_return_value)

    event = events[50]

    self.CheckTimestamp(event.timestamp, '2013-11-04 18:37:36.000399')

    self.assertEqual(event.event_type, 'session end (44903)')

    expected_extra_tokens = {
        'BSM_TOKEN_ARGUMENT32': {
            'is': 12288,
            'num_arg': 3,
            'string': 'am_failure'},
        'BSM_TOKEN_ARGUMENT64': {
            'is': 0,
            'num_arg': 1,
            'string': 'sflags'},
        'BSM_TOKEN_RETURN32': {
            'call_status': 0,
            'error': 'Success',
            'token_status': 0},
        'BSM_TOKEN_SUBJECT32': {
            'aid': 4294967295,
            'egid': 0,
            'euid': 0,
            'gid': 0,
            'pid': 0,
            'session_id': 100015,
            'terminal_ip': '0.0.0.0',
            'terminal_port': 0,
            'uid': 0},
        'BSM_TOKEN_TRAILER': 125
    }
    self.assertEqual(event.extra_tokens, expected_extra_tokens)

    expected_return_value = {
        'call_status': 0,
        'error': 'Success',
        'token_status': 0
    }
    self.assertEqual(event.return_value, expected_return_value)


class OpenBSMParserTest(test_lib.ParserTestCase):
  """Tests for Basic Security Module (BSM) file parser."""

  @shared_test_lib.skipUnlessHasTestFile(['openbsm.bsm'])
  def testParse(self):
    """Tests the Parse function on a "generic" BSM file."""
    parser = bsm.BSMParser()
    knowledge_base_values = {
        'operating_system': definitions.OPERATING_SYSTEM_LINUX}
    storage_writer = self._ParseFile(
        ['openbsm.bsm'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 50)

    events = list(storage_writer.GetEvents())

    expected_extra_tokens = [
        {'BSM_TOKEN_ARGUMENT32': {
            'is': 2882400000,
            'num_arg': 3,
            'string': 'test_arg32_token'},
         'BSM_TOKEN_TRAILER': 50},
        {'BSM_TOKEN_DATA':{
            'data': 'SomeData',
            'format': 'String'},
         'BSM_TOKEN_TRAILER': 39},
        {'BSM_TOKEN_FILE': {
            'string': 'test',
            'timestamp': '1970-01-01 20:42:45.000424'},
         'BSM_TOKEN_TRAILER': 41},
        {'BSM_TOKEN_ADDR': '192.168.100.15',
         'BSM_TOKEN_TRAILER': 30},
        {'BSM_TOKEN_TRAILER': 46,
         'IPv4_Header': '0x400000145478000040010000c0a8649bc0a86e30]'},
        {'BSM_TOKEN_IPC': {
            'object_id': 305419896,
            'object_type': 1},
         'BSM_TOKEN_TRAILER': 31},
        {'BSM_TOKEN_PORT': 20480,
         'BSM_TOKEN_TRAILER': 28},
        {'BSM_TOKEN_OPAQUE': 'aabbccdd',
         'BSM_TOKEN_TRAILER': 32},
        {'BSM_TOKEN_PATH': '/test/this/is/a/test',
         'BSM_TOKEN_TRAILER': 49},
        {'BSM_TOKEN_PROCESS32': {
            'aid': 305419896,
            'egid': 591751049,
            'euid': 19088743,
            'gid': 159868227,
            'pid': 321140038,
            'session_id': 2542171492,
            'terminal_ip': '127.0.0.1',
            'terminal_port': 374945606,
            'uid': 2557891634},
         'BSM_TOKEN_TRAILER': 62},
        {'BSM_TOKEN_PROCESS64': {
            'aid': 305419896,
            'egid': 591751049,
            'euid': 19088743,
            'gid': 159868227,
            'pid': 321140038,
            'session_id': 2542171492,
            'terminal_ip': '127.0.0.1',
            'terminal_port': 374945606,
            'uid': 2557891634},
         'BSM_TOKEN_TRAILER': 66},
        {'BSM_TOKEN_RETURN32': {
            'call_status': 305419896,
            'error': 'Invalid argument',
            'token_status': 22},
         'BSM_TOKEN_TRAILER': 31},
        {'BSM_TOKEN_SEQUENCE': 305419896,
         'BSM_TOKEN_TRAILER': 30},
        {'BSM_TOKEN_AUT_SOCKINET32_EX':{
            'from': '127.0.0.1',
            'from_port': 0,
            'to': '127.0.0.1',
            'to_port': 0},
         'BSM_TOKEN_TRAILER': 44},
        {'BSM_TOKEN_SUBJECT32': {
            'aid': 305419896,
            'egid': 591751049,
            'euid': 19088743,
            'gid': 159868227,
            'pid': 321140038,
            'session_id': 2542171492,
            'terminal_ip': '127.0.0.1',
            'terminal_port': 374945606,
            'uid': 2557891634},
         'BSM_TOKEN_TRAILER': 62},
        {'BSM_TOKEN_SUBJECT32_EX': {
            'aid': 305419896,
            'egid': 591751049,
            'euid': 19088743,
            'gid': 159868227,
            'pid': 321140038,
            'session_id': 2542171492,
            'terminal_ip': 'fe80::1',
            'terminal_port': 374945606,
            'uid': 2557891634},
         'BSM_TOKEN_TRAILER': 78},
        {'BSM_TOKEN_TEXT': 'This is a test.',
         'BSM_TOKEN_TRAILER': 44},
        {'BSM_TOKEN_TRAILER': 37,
         'BSM_TOKEN_ZONENAME': 'testzone'},
        {'BSM_TOKEN_RETURN32': {
            'call_status': 4294967295,
            'error':
            'Argument list too long',
            'token_status': 7},
         'BSM_TOKEN_TRAILER': 31}
    ]

    for event_index in range(0, 19):
      event = events[event_index]
      expected_extra_tokens_dict = expected_extra_tokens[event_index]
      extra_tokens_dict = getattr(event, 'extra_tokens', {})
      self.CheckDictContents(extra_tokens_dict, expected_extra_tokens_dict)


if __name__ == '__main__':
  unittest.main()
