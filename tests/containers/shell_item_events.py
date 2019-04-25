#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the shell item event attribute container."""

from __future__ import unicode_literals

import unittest

from plaso.containers import shell_item_events

from tests import test_lib as shared_test_lib


class ShellItemFileEntryEventDataTest(shared_test_lib.BaseTestCase):
  """Tests for the shell item event attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = shell_item_events.ShellItemFileEntryEventData()

    expected_attribute_names = [
        'data_type', 'file_reference', 'localized_name', 'long_name',
        'name', 'offset', 'origin', 'query', 'shell_item_path']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
