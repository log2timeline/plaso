#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Firefox history event formatter."""

import unittest

from plaso.formatters import firefox

from tests.formatters import test_lib


class FirefoxBookmarkAnnotationFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Firefox bookmark annotation event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = firefox.FirefoxBookmarkAnnotationFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = firefox.FirefoxBookmarkAnnotationFormatter()

    expected_attribute_names = [u'content', u'title', u'url']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


class FirefoxBookmarkFolderFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Firefox bookmark folder event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = firefox.FirefoxBookmarkFolderFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = firefox.FirefoxBookmarkFolderFormatter()

    expected_attribute_names = [u'title']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


class FirefoxBookmarkFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Firefox URL bookmark event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = firefox.FirefoxBookmarkFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = firefox.FirefoxBookmarkFormatter()

    expected_attribute_names = [
        u'type', u'title', u'url', u'places_title', u'visit_count']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


class FirefoxPageVisitFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Firefox page visited event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = firefox.FirefoxPageVisitFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = firefox.FirefoxPageVisitFormatter()

    expected_attribute_names = [
        u'url', u'title', u'visit_count', u'host', u'extra_string']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


class FirefoxDowloadFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Firefox download event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = firefox.FirefoxDowloadFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = firefox.FirefoxDowloadFormatter()

    expected_attribute_names = [
        u'url', u'full_path', u'received_bytes', u'total_bytes']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


if __name__ == '__main__':
  unittest.main()
