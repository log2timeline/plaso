#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event data timeliner."""

import unittest

from plaso.containers import events
from plaso.engine import timeliner

from tests import test_lib as shared_test_lib
from tests.engine import test_lib


class TestEventData(events.EventData):
  """Test event data.

  Attributes:
    access_time (dfdatetime.DateTimeValues): access date and time.
    value (str): value.
  """

  DATA_TYPE = 'test:fs:stat'

  def __init__(self):
    """Initializes event data."""
    super(TestEventData, self).__init__(data_type=self.DATA_TYPE)
    self.access_time = None
    self.value = None


class EventDataTimelinerTest(test_lib.EngineTestCase):
  """Tests for the event data timeliner."""

  # pylint: disable=protected-access

  def testProcessEventData(self):
    """Tests the ProcessEventData function."""
    knowledge_base = self._CreateKnowledgeBase()
    event_data_timeliner = timeliner.EventDataTimeliner(
        knowledge_base, data_location=shared_test_lib.TEST_DATA_PATH)

    event_data = TestEventData()
    event_data.value = 'MyValue'

    self.assertEqual(event_data_timeliner.number_of_produced_events, 0)

    storage_writer = self._CreateStorageWriter()

    event_data_timeliner.ProcessEventData(storage_writer, event_data)

    self.assertEqual(event_data_timeliner.number_of_produced_events, 1)

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
