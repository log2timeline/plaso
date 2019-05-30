#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the syslog file event formatter."""

from __future__ import unicode_literals

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
        'reporter',
        'pid',
        'body',
        'severity']

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

    expected_attribute_names = ['body']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

    # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
