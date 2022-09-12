#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Viminfo parser."""

import unittest

from plaso.parsers import viminfo
from plaso.containers import warnings

from tests.parsers import test_lib


class ViminfoParserTest(test_lib.ParserTestCase):
  """Tests for the Viminfo parser."""

  # pylint: disable=protected-access

  def testParse(self):
    """Tests the Parse function."""
    parser = viminfo.VimInfoParser()
    storage_writer = self._ParseFile(['.viminfo'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 10)

    extraction_warnings = list(storage_writer.GetAttributeContainers(
        warnings.ExtractionWarning.CONTAINER_TYPE))

    self.assertEqual(
        extraction_warnings[0].message,
        'unable to parse log line: \'> ~\\\\_vimrc\'')
    self.assertEqual(
        extraction_warnings[3].message,
        'unable to parse log line: '
        '\'> C:\\\\Program Files (x86)\\\\Vim\\\\.vimrc\'')

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'date_time': '2009-02-13 23:31:30',
        'data_type': 'viminfo:history',
        'history_type': 'Command Line History',
        'history_value': 'e TEST',
        'item_number': 0}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'date_time': '2009-02-13 23:31:31',
        'data_type': 'viminfo:history',
        'history_type': 'Command Line History',
        'history_value': 'version',
        'item_number': 1}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'date_time': '2009-02-13 23:31:32',
        'data_type': 'viminfo:history',
        'history_type': 'Search String History',
        'history_value': '/test_search',
        'item_number': 0}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'date_time': '2009-02-13 23:31:33',
        'data_type': 'viminfo:history',
        'history_type': 'Search String History',
        'history_value': '/ignore',
        'item_number': 1}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'date_time': '2009-02-13 23:31:34',
        'data_type': 'viminfo:history',
        'history_type': 'Register',
        'history_value': 'test register',
        'item_number': '0'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'date_time': '2009-02-13 23:31:35',
        'data_type': 'viminfo:history',
        'history_type': 'Register',
        'history_value': 'test multiline register1\ntest multiline register2',
        'item_number': '1'}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'date_time': '2009-02-13 23:31:36',
        'data_type': 'viminfo:history',
        'history_type': 'File mark',
        'filename': '~\\_vimrc',
        'item_number': 0}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'date_time': '2009-02-13 23:31:37',
        'data_type': 'viminfo:history',
        'history_type': 'File mark',
        'filename': 'C:\\Program Files (x86)\\Vim\\.vimrc',
        'item_number': 1}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)

    expected_event_values = {
        'date_time': '2009-02-13 23:31:38',
        'data_type': 'viminfo:history',
        'history_type': 'Jumplist',
        'filename': '~\\_vimrc',
        'item_number': 0}

    self.CheckEventValues(storage_writer, events[8], expected_event_values)

    expected_event_values = {
        'date_time': '2009-02-13 23:31:39',
        'data_type': 'viminfo:history',
        'history_type': 'Jumplist',
        'filename': 'C:\\Program Files (x86)\\Vim\\.vimrc',
        'item_number': 1}

    self.CheckEventValues(storage_writer, events[9], expected_event_values)


if __name__ == '__main__':
  unittest.main()
