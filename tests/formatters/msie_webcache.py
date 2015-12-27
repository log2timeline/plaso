#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the MSIE WebCache ESE database event formatter."""

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
        u'entry_identifier',
        u'container_identifier',
        u'cache_identifier',
        u'url',
        u'redirect_url',
        u'access_count',
        u'sync_count',
        u'cached_filename',
        u'file_extension',
        u'cached_file_size',
        u'request_headers',
        u'response_headers']

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
        u'container_identifier',
        u'set_identifier',
        u'name',
        u'directory']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
