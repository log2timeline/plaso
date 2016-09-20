#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the dpkg.log formatter."""

import unittest

from tests.formatters import test_lib
from plaso.formatters import dpkg
from plaso.parsers import dpkg as dpkg_parser


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
    mediator = None
    event = dpkg_parser.DpkgLineEvent(
        u'2016-08-09 04:57:14',
        u'status half-installed base-passwd:amd64 3.5.33')

    expected_messages = (
        u'status half-installed base-passwd:amd64 3.5.33',
        u'status half-installed base-passwd:amd64 3.5.33')
    messages = self._formatter.GetMessages(mediator, event)
    self.assertEqual(messages, expected_messages)


if __name__ == '__main__':
  unittest.main()
