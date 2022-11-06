#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event data timeliner."""

import unittest

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.engine import timeliner

from tests import test_lib as shared_test_lib
from tests.engine import test_lib


class TestEventData1(events.EventData):
  """Test event data.

  Attributes:
    access_time (dfdatetime.DateTimeValues): access date and time.
    value (str): value.
  """

  DATA_TYPE = 'test:fs:stat'

  def __init__(self):
    """Initializes event data."""
    super(TestEventData1, self).__init__(data_type=self.DATA_TYPE)
    self.access_time = None
    self.value = None


class TestEventData2(events.EventData):
  """Test event data.

  Attributes:
    added_time (dfdatetime.DateTimeValues): added date and time.
    value (str): value.
  """

  DATA_TYPE = 'test:log:entry'

  def __init__(self):
    """Initializes event data."""
    super(TestEventData2, self).__init__(data_type=self.DATA_TYPE)
    self.access_time = None
    self.value = None


class EventDataTimelinerTest(test_lib.EngineTestCase):
  """Tests for the event data timeliner."""

  # pylint: disable=protected-access

  def testGetEvent(self):
    """Tests the _GetEvent function."""
    knowledge_base = self._CreateKnowledgeBase()
    event_data_timeliner = timeliner.EventDataTimeliner(
        knowledge_base, data_location=shared_test_lib.TEST_DATA_PATH)

    event_data = TestEventData1()
    event_data.value = 'MyValue'

    event_data_identifier = event_data.GetIdentifier()

    # Test date time.
    date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
        time_elements_tuple=(2010, 8, 12, 20, 6, 31, 429876))

    event = event_data_timeliner._GetEvent(
        date_time, 'Test Time', event_data_identifier, 2009)
    self.assertIsNotNone(event)
    self.assertIsNotNone(event.date_time)
    self.assertEqual(event.date_time.year, 2010)
    self.assertEqual(event.timestamp, 1281643591429876)

    date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
        time_elements_tuple=(2010, 8, 12, 20, 6, 31, 429876))

    # Test date time delta.
    date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
        is_delta=True, time_elements_tuple=(1, 8, 12, 20, 6, 31, 429876))

    event = event_data_timeliner._GetEvent(
        date_time, 'Test Time', event_data_identifier, 2009)
    self.assertIsNotNone(event)
    self.assertIsNotNone(event.date_time)
    self.assertEqual(event.date_time.year, 2010)
    self.assertEqual(event.timestamp, 1281643591429876)

    date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
        is_delta=True, time_elements_tuple=(1, 8, 12, 20, 6, 31, 429876))

    event = event_data_timeliner._GetEvent(
        date_time, 'Test Time', event_data_identifier, None)
    self.assertIsNotNone(event)
    self.assertIsNotNone(event.date_time)
    self.assertEqual(event.date_time.year, 1)
    self.assertEqual(event.timestamp, -62116257208570124)

  def testProcessEventData(self):
    """Tests the ProcessEventData function."""
    knowledge_base = self._CreateKnowledgeBase()

    # Test creating an event.
    event_data_timeliner = timeliner.EventDataTimeliner(
        knowledge_base, data_location=shared_test_lib.TEST_DATA_PATH)

    event_data = TestEventData1()
    event_data.access_time = (
        dfdatetime_time_elements.TimeElementsInMicroseconds(
            time_elements_tuple=(2010, 8, 12, 20, 6, 31, 429876)))
    event_data.value = 'MyValue'

    self.assertEqual(event_data_timeliner.number_of_produced_events, 0)

    storage_writer = self._CreateStorageWriter()

    event_data_timeliner.ProcessEventData(storage_writer, event_data)

    self.assertEqual(event_data_timeliner.number_of_produced_events, 1)

    # Test creating a placeholder event.
    event_data_timeliner = timeliner.EventDataTimeliner(
        knowledge_base, data_location=shared_test_lib.TEST_DATA_PATH)

    event_data = TestEventData1()
    event_data.value = 'MyValue'

    self.assertEqual(event_data_timeliner.number_of_produced_events, 0)

    storage_writer = self._CreateStorageWriter()

    event_data_timeliner.ProcessEventData(storage_writer, event_data)

    self.assertEqual(event_data_timeliner.number_of_produced_events, 1)

    # Test creating no placeholder event.
    event_data_timeliner = timeliner.EventDataTimeliner(
        knowledge_base, data_location=shared_test_lib.TEST_DATA_PATH)

    event_data = TestEventData2()
    event_data.value = 'MyValue'

    self.assertEqual(event_data_timeliner.number_of_produced_events, 0)

    storage_writer = self._CreateStorageWriter()

    event_data_timeliner.ProcessEventData(storage_writer, event_data)

    self.assertEqual(event_data_timeliner.number_of_produced_events, 0)

  def testSetPreferredTimeZone(self):
    """Tests the SetPreferredTimeZone function."""
    knowledge_base = self._CreateKnowledgeBase()
    event_data_timeliner = timeliner.EventDataTimeliner(
        knowledge_base, data_location=shared_test_lib.DATA_PATH)

    event_data_timeliner.SetPreferredTimeZone('Europe/Amsterdam')

    self.assertEqual(event_data_timeliner._time_zone.zone, 'Europe/Amsterdam')

    event_data_timeliner.SetPreferredTimeZone(None)

    self.assertEqual(event_data_timeliner._time_zone.zone, 'Etc/UTC')


if __name__ == '__main__':
  unittest.main()
