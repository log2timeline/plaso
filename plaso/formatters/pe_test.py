#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the PE event formatters."""

import unittest

from plaso.formatters import pe
from plaso.formatters import test_lib


class PECompilationTimeFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the PE compilation time formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = pe.PECompilationFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = pe.PECompilationFormatter()

    expected_attribute_names = [
        u'pe_type',
        u'imphash',]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class PEImportTimeFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the PE import time formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = pe.PEImportFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = pe.PEImportFormatter()

    expected_attribute_names = [
        u'dll_name',
        u'pe_type',
        u'imphash',]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class PEDelayImportFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the PE delay import formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = pe.PEDelayImportFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = pe.PEDelayImportFormatter()

    expected_attribute_names = [
        u'dll_name',
        u'pe_type',
        u'imphash',]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class PEResourceCreationFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the PE resource creation formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = pe.PEResourceCreationFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = pe.PEResourceCreationFormatter()

    expected_attribute_names = [
        u'pe_type',
        u'imphash',]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class PELoadConfigModificationEventTest(test_lib.EventFormatterTestCase):
  """Tests for the PE load configuration formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = pe.PELoadConfigModificationEvent()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = pe.PELoadConfigModificationEvent()

    expected_attribute_names = [
        u'pe_type',
        u'imphash',]

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
