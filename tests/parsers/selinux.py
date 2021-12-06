#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the selinux log file parser."""

import unittest

from plaso.parsers import selinux

from tests.parsers import test_lib


class SELinuxUnitTest(test_lib.ParserTestCase):
  """Tests for the selinux log file parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = selinux.SELinuxParser()
    knowledge_base_values = {'year': 2013}
    storage_writer = self._ParseFile(
        ['selinux.log'], parser,
        knowledge_base_values=knowledge_base_values)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 7)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # Test case: normal entry.
    expected_event_values = {
        'audit_type': 'LOGIN',
        'body': (
            'pid=25443 uid=0 old auid=4294967295 new auid=0 old ses=4294967295 '
            'new ses=1165'),
        'date_time': '2012-05-24 07:40:01.174000',
        'data_type': 'selinux:line',
        'pid': '25443'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # Test case: short date.
    expected_event_values = {
        'audit_type': 'SHORTDATE',
        'body': 'check rounding',
        'date_time': '2012-05-24 07:40:01.000000',
        'data_type': 'selinux:line'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    # Test case: no message.
    expected_event_values = {
        'audit_type': 'NOMSG',
        'date_time': '2012-05-24 07:40:22.174000',
        'data_type': 'selinux:line'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    # Test case: under score.
    expected_event_values = {
        'audit_type': 'UNDER_SCORE',
        'body': (
            'pid=25444 uid=0 old auid=4294967295 new auid=54321 old '
            'ses=4294967295 new ses=1166'),
        'date_time': '2012-05-24 07:47:46.174000',
        'data_type': 'selinux:line',
        'pid': '25444'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)


if __name__ == '__main__':
  unittest.main()
