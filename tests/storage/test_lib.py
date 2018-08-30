# -*- coding: utf-8 -*-
"""Storage related functions and classes for testing."""

from __future__ import unicode_literals

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.lib import timelib

from tests import test_lib as shared_test_lib


class StorageTestCase(shared_test_lib.BaseTestCase):
  """The unit test case for a storage object."""

  # pylint: disable=protected-access

  def _CreateTestEvents(self):
    """Creates events for testing.

    Returns:
      list[EventObject]: events.
    """
    test_events = []
    filetime = dfdatetime_filetime.Filetime()

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = 'MY AutoRun key'
    event_data.parser = 'UNKNOWN'
    event_data.regvalue = {'Value': 'c:/Temp/evil.exe'}

    filetime.CopyFromDateTimeString('2012-04-20 22:38:46.929596')
    event = time_events.DateTimeValuesEvent(
        filetime, definitions.TIME_DESCRIPTION_WRITTEN)

    self._MergeEventAndEventData(event, event_data)
    test_events.append(event)

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = (
        'HKEY_CURRENT_USER\\Secret\\EvilEmpire\\Malicious_key')
    event_data.parser = 'UNKNOWN'
    event_data.regvalue = {'Value': 'send all the exes to the other world'}

    filetime.CopyFromDateTimeString('2012-04-20 23:56:46.929596')
    event = time_events.DateTimeValuesEvent(
        filetime, definitions.TIME_DESCRIPTION_WRITTEN)

    self._MergeEventAndEventData(event, event_data)
    test_events.append(event)

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = 'HKEY_CURRENT_USER\\Windows\\Normal'
    event_data.parser = 'UNKNOWN'
    event_data.regvalue = {'Value': 'run all the benign stuff'}

    filetime.CopyFromDateTimeString('2012-04-20 16:44:46')
    event = time_events.DateTimeValuesEvent(
        filetime, definitions.TIME_DESCRIPTION_WRITTEN)

    self._MergeEventAndEventData(event, event_data)
    test_events.append(event)

    timestamp = timelib.Timestamp.CopyFromString('2009-04-05 12:27:39')

    # TODO: refactor to use event data.
    event = time_events.TimestampEvent(
        timestamp, definitions.TIME_DESCRIPTION_WRITTEN,
        data_type='text:entry')
    event.hostname = 'nomachine'
    event.offset = 12
    event.parser = 'UNKNOWN'
    event.text = (
        'This is a line by someone not reading the log line properly. And '
        'since this log line exceeds the accepted 80 chars it will be '
        'shortened.')
    event.username = 'johndoe'
    test_events.append(event)

    return test_events

  def _CreateTestEventTags(self, test_events):
    """Creates the event tags for testing.

    Args:
      list[EventObject]: test_events.

    Returns:
      list[EventTag]: event tags.
    """
    event_tags = []

    event_identifier = test_events[0].GetIdentifier()

    event_tag = events.EventTag(comment='My comment')
    event_tag.SetEventIdentifier(event_identifier)
    event_tags.append(event_tag)

    event_identifier = test_events[1].GetIdentifier()

    event_tag = events.EventTag()
    event_tag.SetEventIdentifier(event_identifier)
    event_tag.AddLabel('Malware')
    event_tags.append(event_tag)

    event_identifier = test_events[2].GetIdentifier()

    event_tag = events.EventTag(comment='This is interesting')
    event_tag.SetEventIdentifier(event_identifier)
    event_tag.AddLabels(['Malware', 'Benign'])
    event_tags.append(event_tag)

    event_identifier = test_events[1].GetIdentifier()

    event_tag = events.EventTag()
    event_tag.SetEventIdentifier(event_identifier)
    event_tag.AddLabel('Interesting')
    event_tags.append(event_tag)

    return event_tags

  # TODO: remove after event data refactor.
  def _MergeEventAndEventData(self, event, event_data):
    """Merges the event data with the event.

    args:
      event (EventObject): event.
      event_data (EventData): event_data.
    """
    for attribute_name, attribute_value in event_data.GetAttributes():
      setattr(event, attribute_name, attribute_value)
