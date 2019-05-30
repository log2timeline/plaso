#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MSIE WebCache ESE database event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import msie_webcache

from tests.formatters import test_lib


class MsieWebCacheContainerEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the WebCache Container_# table record event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = msie_webcache.MsieWebCacheContainerEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = msie_webcache.MsieWebCacheContainerEventFormatter()

    expected_attribute_names = [
        'entry_identifier',
        'container_identifier',
        'cache_identifier',
        'url',
        'redirect_url',
        'access_count',
        'sync_count',
        'cached_filename',
        'file_extension',
        'cached_file_size',
        'request_headers',
        'response_headers']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class MsieWebCacheContainersEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the WebCache Containers table record event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = msie_webcache.MsieWebCacheContainersEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = msie_webcache.MsieWebCacheContainersEventFormatter()

    expected_attribute_names = [
        'container_identifier',
        'set_identifier',
        'name',
        'directory']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
