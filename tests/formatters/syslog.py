#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the syslog file event formatter."""

import unittest

from plaso.formatters import syslog

from tests.formatters import test_lib


class SyslogLineFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the syslog line event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = syslog.SyslogLineFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = syslog.SyslogLineFormatter()

    expected_attribute_names = [
        u'reporter',
        u'pid',
        u'body']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

    # TODO: add test for GetMessages.


class SyslogCommentFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the syslog comment formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = syslog.SyslogCommentFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = syslog.SyslogCommentFormatter()

    expected_attribute_names = [u'body']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

    # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
