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

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 54)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_extra_tokens = [
        {'AUT_TEXT': {
            'text': 'launchctl::Audit recovery'}},
        {'AUT_PATH': {
            'path': '/var/audit/20131104171720.crash_recovery'}},
        {'AUT_RETURN32': {
            'call_status': 0,
            'error': 'Success',
            'token_status': 0}}]

    expected_event_values = {
        'data_type': 'bsm:entry',
        'event_type': 45029,
        'extra_tokens': expected_extra_tokens,
        'return_value': (
            '{\'error\': \'Success\', \'token_status\': 0, '
            '\'call_status\': 0}'),
        'written_time': '2013-11-04T18:36:20.000381+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


class OpenBSMParserTest(test_lib.ParserTestCase):
  """Tests for Basic Security Module (BSM) file parser."""

  def testParse(self):
    """Tests the Parse function on a "generic" BSM file."""
    parser = bsm.BSMParser()
    storage_writer = self._ParseFile(['openbsm.bsm'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 50)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_extra_tokens = [{
        'AUT_ARG32': {
            'is': 2882400000,
            'num_arg': 3,
            'string': 'test_arg32_token'}}]

    expected_event_values = {
        'data_type': 'bsm:entry',
        'event_type': 0,
        'extra_tokens': expected_extra_tokens,
        'return_value': None,
        'written_time': '2008-12-28T15:12:18.000131+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
