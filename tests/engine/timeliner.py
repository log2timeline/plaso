#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event data timeliner."""

import unittest

from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.engine import timeliner
from plaso.storage.fake import writer as fake_writer

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

  # pylint: disable=arguments-differ
  def _CreateStorageWriter(self, event_data, base_date=None):
    """Creates a storage writer object.

    Args:
      event_data (EventData): event data.
      base_date (Optional[tuple[int, int, int]]): base date, as tuple of year,
          month and day of month.

    Returns:
      FakeStorageWriter: storage writer.
    """
    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    event_data_stream = events.EventDataStream()
    storage_writer.AddAttributeContainer(event_data_stream)

    event_data_stream_identifier = event_data_stream.GetIdentifier()

    if base_date:
      date_less_log_helper = events.DateLessLogHelper()
      date_less_log_helper.earliest_date = base_date
      date_less_log_helper.last_relative_date = (0, 0, 0)

      date_less_log_helper.SetEventDataStreamIdentifier(
          event_data_stream_identifier)
      storage_writer.AddAttributeContainer(date_less_log_helper)

    event_data.SetEventDataStreamIdentifier(event_data_stream_identifier)
    storage_writer.AddAttributeContainer(event_data)

    return storage_writer

  def testGetBaseDate(self):
    """Tests the _GetBaseDate function."""
    event_data_timeliner = timeliner.EventDataTimeliner(
        data_location=shared_test_lib.TEST_DATA_PATH)

    current_date = event_data_timeliner._GetCurrentDate()

    event_data = TestEventData1()
    event_data.value = 'MyValue'

    # Test with date-less log helper.
    storage_writer = self._CreateStorageWriter(
        event_data, base_date=(2012, 3, 30))

    # Ensure to reset the timeliner base dates cache.
    event_data_timeliner._base_dates = {}

    base_date = event_data_timeliner._GetBaseDate(storage_writer, event_data)
    self.assertEqual(base_date, (2012, 0, 0))

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'timelining_warning')
    self.assertEqual(number_of_warnings, 0)

    # Test missing date-less log helper.
    storage_writer = self._CreateStorageWriter(event_data)

    # Ensure to reset the timeliner base dates cache.
    event_data_timeliner._base_dates = {}

    base_date = event_data_timeliner._GetBaseDate(storage_writer, event_data)
    self.assertEqual(base_date, (current_date[0], 0, 0))

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'timelining_warning')
    self.assertEqual(number_of_warnings, 1)

    # TODO: improve test coverage.

  def testGetCurrentDate(self):
    """Tests the _GetCurrentDate function."""
    event_data_timeliner = timeliner.EventDataTimeliner(
        data_location=shared_test_lib.TEST_DATA_PATH)

    current_date = event_data_timeliner._GetCurrentDate()
    self.assertIsNotNone(current_date)

  def testGetEvent(self):
    """Tests the _GetEvent function."""
    event_data_timeliner = timeliner.EventDataTimeliner(
        data_location=shared_test_lib.TEST_DATA_PATH)

    event_data = TestEventData1()
    event_data.value = 'MyValue'

    # Test a regular date and time value.
    storage_writer = self._CreateStorageWriter(event_data)

    date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
        time_elements_tuple=(2010, 8, 12, 20, 6, 31, 429876))

    # Ensure to reset the timeliner base dates cache.
    event_data_timeliner._base_dates = {}

    event = event_data_timeliner._GetEvent(
        storage_writer, event_data, None, date_time, 'Test Time')
    self.assertIsNotNone(event)
    self.assertIsNotNone(event.date_time)
    self.assertEqual(event.date_time.year, 2010)
    self.assertEqual(event.timestamp, 1281643591429876)

    date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
        time_elements_tuple=(2010, 8, 12, 20, 6, 31, 429876))

    # Test date time delta of February 29 with leap year.
    storage_writer = self._CreateStorageWriter(
        event_data, base_date=(2012, 1, 1))

    date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
        is_delta=True, time_elements_tuple=(0, 2, 29, 20, 6, 31, 429876))

    # Ensure to reset the timeliner base dates cache.
    event_data_timeliner._base_dates = {}

    event = event_data_timeliner._GetEvent(
        storage_writer, event_data, None, date_time, 'Test Time')
    self.assertIsNotNone(event)
    self.assertIsNotNone(event.date_time)
    self.assertEqual(event.date_time.year, 2012)
    self.assertEqual(event.timestamp, 1330545991429876)

    date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
        is_delta=True, time_elements_tuple=(1, 8, 12, 20, 6, 31, 429876))

    # Test date time delta of February 29 with non-leap year.
    storage_writer = self._CreateStorageWriter(
        event_data, base_date=(2013, 1, 1))

    date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
        is_delta=True, time_elements_tuple=(0, 2, 29, 20, 6, 31, 429876))

    # Ensure to reset the timeliner base dates cache.
    event_data_timeliner._base_dates = {}

    event = event_data_timeliner._GetEvent(
        storage_writer, event_data, None, date_time, 'Test Time')
    self.assertIsNotNone(event)
    self.assertIsNotNone(event.date_time)
    self.assertIsInstance(event.date_time, dfdatetime_semantic_time.InvalidTime)

    # Test date time delta without a base date.
    storage_writer = self._CreateStorageWriter(event_data)

    date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
        time_elements_tuple=(4, 2, 29, 20, 6, 31, 429876))

    # Ensure to reset the timeliner base dates cache.
    event_data_timeliner._base_dates = {}

    event = event_data_timeliner._GetEvent(
        storage_writer, event_data, None, date_time, 'Test Time')
    self.assertIsNotNone(event)
    self.assertIsNotNone(event.date_time)
    self.assertEqual(event.date_time.year, 4)
    self.assertEqual(event.timestamp, -62035818808570124)

  # TODO: add tests for _ProduceTimeliningWarning
  # TODO: add tests for _ReadConfigurationFile

  def testProcessEventData(self):
    """Tests the ProcessEventData function."""
    # Test creating an event.
    event_data_timeliner = timeliner.EventDataTimeliner(
        data_location=shared_test_lib.TEST_DATA_PATH)

    event_data = TestEventData1()
    event_data.access_time = (
        dfdatetime_time_elements.TimeElementsInMicroseconds(
            time_elements_tuple=(2010, 8, 12, 20, 6, 31, 429876)))
    event_data.value = 'MyValue'

    self.assertEqual(event_data_timeliner.number_of_produced_events, 0)

    storage_writer = self._CreateStorageWriter(event_data)

    event_data_timeliner.ProcessEventData(storage_writer, event_data, None)

    self.assertEqual(event_data_timeliner.number_of_produced_events, 1)

    # Test creating a placeholder event.
    event_data_timeliner = timeliner.EventDataTimeliner(
        data_location=shared_test_lib.TEST_DATA_PATH)

    event_data = TestEventData1()
    event_data.value = 'MyValue'

    self.assertEqual(event_data_timeliner.number_of_produced_events, 0)

    storage_writer = self._CreateStorageWriter(event_data)

    event_data_timeliner.ProcessEventData(storage_writer, event_data, None)

    self.assertEqual(event_data_timeliner.number_of_produced_events, 1)

    # Test creating no placeholder event.
    event_data_timeliner = timeliner.EventDataTimeliner(
        data_location=shared_test_lib.TEST_DATA_PATH)

    event_data = TestEventData2()
    event_data.value = 'MyValue'

    self.assertEqual(event_data_timeliner.number_of_produced_events, 0)

    storage_writer = self._CreateStorageWriter(event_data)

    event_data_timeliner.ProcessEventData(storage_writer, event_data, None)

    self.assertEqual(event_data_timeliner.number_of_produced_events, 0)

  def testSetPreferredTimeZone(self):
    """Tests the SetPreferredTimeZone function."""
    event_data_timeliner = timeliner.EventDataTimeliner(
        data_location=shared_test_lib.DATA_PATH)

    event_data_timeliner.SetPreferredTimeZone('Europe/Amsterdam')

    self.assertEqual(
        event_data_timeliner._preferred_time_zone.zone, 'Europe/Amsterdam')

    event_data_timeliner.SetPreferredTimeZone(None)

    self.assertIsNone(event_data_timeliner._preferred_time_zone)


if __name__ == '__main__':
  unittest.main()
