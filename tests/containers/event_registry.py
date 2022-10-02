#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event data registry."""

import unittest

from plaso.containers import event_registry
from plaso.containers import events

from tests import test_lib as shared_test_lib


class TestEventData(events.EventData):
  """Test event data."""

  DATA_TYPE = 'test'


class EventDataRegistryTest(shared_test_lib.BaseTestCase):
  """Tests for the event data registry."""

  def testEventDataRegistration(self):
    """Tests the Register and DeregisterEventData functions."""
    # pylint: disable=protected-access
    number_of_classes = len(
        event_registry.EventDataRegistry._event_data_classes)

    event_registry.EventDataRegistry.RegisterEventDataClass(TestEventData)
    self.assertEqual(
        len(event_registry.EventDataRegistry._event_data_classes),
        number_of_classes + 1)

    with self.assertRaises(KeyError):
      event_registry.EventDataRegistry.RegisterEventDataClass(TestEventData)

    event_registry.EventDataRegistry.DeregisterEventDataClass(TestEventData)
    self.assertEqual(
        len(event_registry.EventDataRegistry._event_data_classes),
        number_of_classes)


if __name__ == '__main__':
  unittest.main()
