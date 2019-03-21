# -*- coding: utf-8 -*-
"""Tests for the Google Takeout event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import google_takeout

from tests.formatters import test_lib

class GoogleGmailUpdateEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Google Maps event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = google_takeout.GoogleGmailUpdateEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = google_takeout.GoogleGmailUpdateEventFormatter()

    expected_attribute_names = [
        'mailfrom', 'mailto', 'message_id',
        'cc', 'bcc', 'subject', 'body',
        'user_agent', 'received_by', 'received_from', 'precedence',
        'sender', 'received_spf', 'vbr_info',
        'auth_results', 'arc_seal', 'arc_msg_signature', 'arc_auth_results',
        'auto_submitted', 'in_reply_to', 'return_path']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

class GoogleActivitiesUpdateEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Google Activities event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = google_takeout.GoogleActivitiesUpdateEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = google_takeout.GoogleActivitiesUpdateEventFormatter()

    expected_attribute_names = [
        'header', 'title', 'title_url', 'subtitles', 'details', 'location']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

class GooglePurchasesUpdateEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Google Purchases event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = google_takeout.GooglePurchasesUpdateEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = google_takeout.GooglePurchasesUpdateEventFormatter()

    expected_attribute_names = [
        'order_id', 'merchant', 'product', 'status', 'quantity', 'price',
        'url', 'address', 'departure_airport', 'arrival_airport']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

class GoogleMapsUpdateEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Google Maps event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = google_takeout.GoogleMapsUpdateEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = google_takeout.GoogleMapsUpdateEventFormatter()

    expected_attribute_names = [
        'latitude', 'longitude', 'accuracy', 'velocity', 'heading', 'altitude',
        'vertical_accuracy', 'activity']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

class GoogleChromeHistoryUpdateEventFormatterTest(
    test_lib.EventFormatterTestCase):
  """Tests for the Google Chrome History event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = google_takeout.GoogleChromeHistoryUpdateEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = google_takeout.GoogleChromeHistoryUpdateEventFormatter()

    expected_attribute_names = [
        'title', 'url', 'client_id', 'page_transition']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

class GoogleHangoutsUpdateEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Google Maps event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = google_takeout.GoogleHangoutsUpdateEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = google_takeout.GoogleHangoutsUpdateEventFormatter()

    expected_attribute_names = [
        'conversation_id', 'conversation_name', 'conversation_type',
        'conversation_view', 'conversation_medium', 'user', 'inviter',
        'participant', 'message_type', 'message_text', 'message_photo',
        'conversation_old_name', 'user_added', 'user_removed']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

if __name__ == '__main__':
  unittest.main()
