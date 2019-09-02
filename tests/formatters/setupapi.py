#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Setupapi log event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import setupapi

from tests.formatters import test_lib


class SetupapiLogFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Windows Setupapi log event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = setupapi.SetupapiLogFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = setupapi.SetupapiLogFormatter()

    expected_attribute_names = [
        'entry_type',
        'exit_status']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
