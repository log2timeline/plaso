#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the fseventsd record event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import fseventsd

from tests.formatters import test_lib


class FseventsdFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the fseventsd record event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = fseventsd.FSEventsdEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = fseventsd.FSEventsdEventFormatter()

    expected_attribute_names = [
        'object_type', 'path', 'event_types', 'event_identifier']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


if __name__ == '__main__':
  unittest.main()
