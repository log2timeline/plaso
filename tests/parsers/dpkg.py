#!/usr/bin/env python3
# -*_ coding: utf-8 -*-
"""Tests for the dpkg.Log parser."""

import unittest

from plaso.parsers import dpkg

from tests.parsers import test_lib


class DpkgParserTest(test_lib.ParserTestCase):
  """Tests for the Dpkg Log parser."""

  def testParse(self):
    """Tests for the Parse method."""
    parser = dpkg.DpkgParser()
    storage_writer = self._ParseFile(['dpkg.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'body': 'conffile /etc/X11/Xsession keep',
        'data_type': 'dpkg:line',
        'date_time': '2009-02-25 11:45:23'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'body': 'startup archives install',
        'data_type': 'dpkg:line',
        'date_time': '2016-08-03 15:25:53'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'body': 'install base-passwd:amd64 <none> 3.5.33',
        'data_type': 'dpkg:line',
        'date_time': '2016-08-06 17:35:39'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'body': 'status half-installed base-passwd:amd64 3.5.33',
        'data_type': 'dpkg:line',
        'date_time': '2016-08-09 04:57:14'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

  def testVerification(self):
    """Tests for the VerifyStructure method"""
    mediator = None
    parser = dpkg.DpkgParser()

    valid_lines = (
        '2016-08-09 04:57:14 status half-installed base-passwd:amd64 3.5.33')
    self.assertTrue(parser.VerifyStructure(mediator, valid_lines))

    invalid_lines = (
        '2016-08-09 04:57:14 X status half-installed base-passwd:amd64 3.5.33')
    self.assertFalse(parser.VerifyStructure(mediator, invalid_lines))


if __name__ == '__main__':
  unittest.main()
