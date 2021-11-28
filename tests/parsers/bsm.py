#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Basic Security Module (BSM) file parser."""

import unittest

from plaso.parsers import bsm

from tests.parsers import test_lib


class MacOSBSMParserTest(test_lib.ParserTestCase):
  """Tests for Basic Security Module (BSM) file parser."""

  def testParse(self):
    """Tests the Parse function on a MacOS BSM file."""
    parser = bsm.BSMParser()
    storage_writer = self._ParseFile(['apple.bsm'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 54)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_extra_tokens = [
        {'AUT_TEXT': {
            'text': 'launchctl::Audit recovery'}},
        {'AUT_PATH': {
            'path': '/var/audit/20131104171720.crash_recovery'}},
        {'AUT_RETURN32': {
            'call_status': 0,
            'error': 'Success',
            'token_status': 0}}]

    expected_return_value = (
        '{\'error\': \'Success\', \'token_status\': 0, \'call_status\': 0}')

    expected_event_values = {
        'data_type': 'bsm:event',
        'date_time': '2013-11-04 18:36:20.000381',
        'event_type': 45029,
        'extra_tokens': expected_extra_tokens,
        'return_value': expected_return_value}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_extra_tokens = [
        {'AUT_SUBJECT32': {
            'aid': -1,
            'egid': 92,
            'euid': 92,
            'gid': 92,
            'pid': 143,
            'session_id': 100004,
            'terminal_ip': '0.0.0.0',
            'terminal_port': 143,
            'uid': 92}},
        {'AUT_TEXT': {
            'text': ('Verify password for record type Users \'moxilo\' node '
                     '\'/Local/Default\'')}},
        {'AUT_RETURN32': {
            'call_status': 5000,
            'error': 'UNKNOWN',
            'token_status': 255}}]

    expected_return_value = (
        '{\'error\': \'UNKNOWN\', \'token_status\': 255, '
        '\'call_status\': 5000}')

    expected_event_values = {
        'data_type': 'bsm:event',
        'date_time': '2013-11-04 18:36:26.000171',
        'event_type': 45023,
        'extra_tokens': expected_extra_tokens,
        'return_value': expected_return_value}

    self.CheckEventValues(storage_writer, events[15], expected_event_values)

    expected_extra_tokens = [
        {'AUT_SUBJECT32': {
            'aid': -1,
            'egid': 0,
            'euid': 0,
            'gid': 0,
            'pid': 67,
            'session_id': 100004,
            'terminal_ip': '0.0.0.0',
            'terminal_port': 67,
            'uid': 0}},
        {'AUT_TEXT': {
            'text': 'system.login.done'}},
        {'AUT_TEXT': {
            'text': 'system.login.done'}},
        {'AUT_RETURN32': {
            'call_status': 0,
            'error': 'Success',
            'token_status': 0}}]

    expected_return_value = (
        '{\'error\': \'Success\', \'token_status\': 0, \'call_status\': 0}')

    expected_event_values = {
        'data_type': 'bsm:event',
        'date_time': '2013-11-04 18:36:26.000530',
        'event_type': 45025,
        'extra_tokens': expected_extra_tokens,
        'return_value': expected_return_value}

    self.CheckEventValues(storage_writer, events[31], expected_event_values)

    expected_extra_tokens = [
        {'AUT_ARG64': {
            'is': 0,
            'num_arg': 1,
            'string': 'sflags'}},
        {'AUT_ARG32': {
            'is': 12288,
            'num_arg': 2,
            'string': 'am_success'}},
        {'AUT_ARG32': {
            'is': 12288,
            'num_arg': 3,
            'string': 'am_failure'}},
        {'AUT_SUBJECT32': {
            'aid': -1,
            'egid': 0,
            'euid': 0,
            'gid': 0,
            'pid': 0,
            'session_id': 100015,
            'terminal_ip': '0.0.0.0',
            'terminal_port': 0,
            'uid': 0}},
        {'AUT_RETURN32': {
            'call_status': 0,
            'error': 'Success',
            'token_status': 0}}]

    expected_return_value = (
        '{\'error\': \'Success\', \'token_status\': 0, \'call_status\': 0}')

    expected_event_values = {
        'data_type': 'bsm:event',
        'date_time': '2013-11-04 18:37:36.000399',
        'event_type': 44903,
        'extra_tokens': expected_extra_tokens,
        'return_value': expected_return_value}

    self.CheckEventValues(storage_writer, events[50], expected_event_values)


class OpenBSMParserTest(test_lib.ParserTestCase):
  """Tests for Basic Security Module (BSM) file parser."""

  def testParse(self):
    """Tests the Parse function on a "generic" BSM file."""
    parser = bsm.BSMParser()
    storage_writer = self._ParseFile(['openbsm.bsm'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 50)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_extra_tokens = [
        [{'AUT_ARG32': {
            'is': 2882400000,
            'num_arg': 3,
            'string': 'test_arg32_token'}}],
        [{'AUT_DATA':{
            'data': 'SomeData',
            'format': 'String'}}],
        [{'AUT_OTHER_FILE32': {
            'string': 'test',
            'timestamp': '1970-01-01 20:42:45.000424'}}],
        [{'AUT_IN_ADDR': {
            'ip': '192.168.100.15'}}],
        [{'AUT_IP': {
            'IPv4_Header': '400000145478000040010000c0a8649bc0a86e30'}}],
        [{'AUT_IPC': {
            'object_id': 305419896,
            'object_type': 1}}],
        [{'AUT_IPORT': {
            'port_number': 20480}}],
        [{'AUT_OPAQUE': {
            'data': 'aabbccdd'}}],
        [{'AUT_PATH': {
            'path': '/test/this/is/a/test'}}],
        [{'AUT_PROCESS32': {
            'aid': 305419896,
            'egid': 591751049,
            'euid': 19088743,
            'gid': 159868227,
            'pid': 321140038,
            'session_id': 2542171492,
            'terminal_ip': '127.0.0.1',
            'terminal_port': 374945606,
            'uid': -1737075662}}],
        [{'AUT_PROCESS64': {
            'aid': 305419896,
            'egid': 591751049,
            'euid': 19088743,
            'gid': 159868227,
            'pid': 321140038,
            'session_id': 2542171492,
            'terminal_ip': '127.0.0.1',
            'terminal_port': 374945606,
            'uid': -1737075662}}],
        [{'AUT_RETURN32': {
            'call_status': 305419896,
            'error': 'Invalid argument',
            'token_status': 22}}],
        [{'AUT_SEQ': {
            'sequence_number': 305419896}}],
        [{'AUT_SOCKET_EX':{
            'from': '127.0.0.1',
            'from_port': 0,
            'to': '127.0.0.1',
            'to_port': 0}}],
        [{'AUT_SUBJECT32': {
            'aid': 305419896,
            'egid': 591751049,
            'euid': 19088743,
            'gid': 159868227,
            'pid': 321140038,
            'session_id': 2542171492,
            'terminal_ip': '127.0.0.1',
            'terminal_port': 374945606,
            'uid': -1737075662}}],
        [{'AUT_SUBJECT32_EX': {
            'aid': 305419896,
            'egid': 591751049,
            'euid': 19088743,
            'gid': 159868227,
            'pid': 321140038,
            'session_id': 2542171492,
            'terminal_ip': 'fe80:0000:0000:0000:0000:0000:0000:0001',
            'terminal_port': 374945606,
            'uid': -1737075662}}],
        [{'AUT_TEXT': {'text': 'This is a test.'}}],
        [{'AUT_ZONENAME': {'name': 'testzone'}}],
        [{'AUT_RETURN32': {
            'call_status': -1,
            'error':
            'Argument list too long',
            'token_status': 7}}]
    ]

    for event_index, expected_extra_tokens_dict in enumerate(
        expected_extra_tokens):
      event = events[event_index]
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      self.assertEqual(event_data.extra_tokens, expected_extra_tokens_dict)


if __name__ == '__main__':
  unittest.main()
