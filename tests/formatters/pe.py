#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the PE event formatters."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import pe

from tests.formatters import test_lib


class PECompilationTimeFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the PE compilation time formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = pe.PECompilationFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = pe.PECompilationFormatter()

    expected_attribute_names = [
        'pe_type',
        'imphash',]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class PEImportTimeFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the PE import time formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = pe.PEImportFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = pe.PEImportFormatter()

    expected_attribute_names = [
        'dll_name',
        'pe_type',
        'imphash',]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class PEDelayImportFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the PE delay import formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = pe.PEDelayImportFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = pe.PEDelayImportFormatter()

    expected_attribute_names = [
        'dll_name',
        'pe_type',
        'imphash',]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class PEResourceCreationFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the PE resource creation formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = pe.PEResourceCreationFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = pe.PEResourceCreationFormatter()

    expected_attribute_names = [
        'pe_type',
        'imphash',]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class PELoadConfigModificationEventTest(test_lib.EventFormatterTestCase):
  """Tests for the PE load configuration formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = pe.PELoadConfigModificationEvent()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = pe.PELoadConfigModificationEvent()

    expected_attribute_names = [
        'pe_type',
        'imphash',]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
