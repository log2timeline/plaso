#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Firefox history event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import firefox

from tests.formatters import test_lib


class FirefoxBookmarkAnnotationFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Firefox bookmark annotation event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = firefox.FirefoxBookmarkAnnotationFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = firefox.FirefoxBookmarkAnnotationFormatter()

    expected_attribute_names = ['content', 'title', 'url']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


class FirefoxBookmarkFolderFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Firefox bookmark folder event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = firefox.FirefoxBookmarkFolderFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = firefox.FirefoxBookmarkFolderFormatter()

    expected_attribute_names = ['title']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


class FirefoxBookmarkFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Firefox URL bookmark event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = firefox.FirefoxBookmarkFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = firefox.FirefoxBookmarkFormatter()

    expected_attribute_names = [
        'type', 'title', 'url', 'places_title', 'visit_count']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


class FirefoxPageVisitFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Firefox page visited event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = firefox.FirefoxPageVisitFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = firefox.FirefoxPageVisitFormatter()

    expected_attribute_names = [
        'url', 'title', 'visit_count', 'host', 'extra_string']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


class FirefoxDowloadFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Firefox download event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = firefox.FirefoxDowloadFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = firefox.FirefoxDowloadFormatter()

    expected_attribute_names = [
        'url', 'full_path', 'received_bytes', 'total_bytes']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


if __name__ == '__main__':
  unittest.main()
