#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the dpkg.log formatter."""

import unittest

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import time_events
from plaso.formatters import dpkg
from plaso.lib import definitions
from tests.formatters import test_lib


class DpkgFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the dpkg.log event formatter."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._formatter = dpkg.DpkgFormatter()

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    expected_attribute_names = [
        u'body']

    self._TestGetFormatStringAttributeNames(
        self._formatter, expected_attribute_names)

  def testGetMessages(self):
    """Tests the GetMessages method."""
    date_time = dfdatetime_posix_time.PosixTime()
    date_time.CopyFromString(u'2016-08-09 04:57:14')

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
    event.data_type = u'dpkg:line'
    event.body = u'status half-installed base-passwd:amd64 3.5.33'

    expected_messages = (
        u'status half-installed base-passwd:amd64 3.5.33',
        u'status half-installed base-passwd:amd64 3.5.33')
    messages = self._formatter.GetMessages(None, event)
    self.assertEqual(messages, expected_messages)


if __name__ == '__main__':
  unittest.main()
