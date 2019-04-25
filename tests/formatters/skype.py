#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Skype main database event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import skype

from tests.formatters import test_lib


class SkypeAccountFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Skype account event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = skype.SkypeAccountFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = skype.SkypeAccountFormatter()

    expected_attribute_names = [
        'username',
        'email',
        'country']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class SkypeChatFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Skype chat event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = skype.SkypeChatFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = skype.SkypeChatFormatter()

    expected_attribute_names = [
        'from_account',
        'to_account',
        'title',
        'text']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class SkypeSMSFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Skype SMS event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = skype.SkypeSMSFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = skype.SkypeSMSFormatter()

    expected_attribute_names = [
        'number',
        'text']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class SkypeCallFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Skype call event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = skype.SkypeCallFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = skype.SkypeCallFormatter()

    expected_attribute_names = [
        'src_call',
        'dst_call',
        'call_type']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class SkypeTransferFileFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Skype transfer file event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = skype.SkypeTransferFileFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = skype.SkypeTransferFileFormatter()

    expected_attribute_names = [
        'source',
        'destination',
        'transferred_filename',
        'action_type']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
