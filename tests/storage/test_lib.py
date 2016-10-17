# -*- coding: utf-8 -*-
"""Storage related functions and classes for testing."""

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.containers import text_events
from plaso.containers import windows_events
from plaso.lib import timelib

from tests import test_lib as shared_test_lib


class StorageTestCase(shared_test_lib.BaseTestCase):
  """The unit test case for a storage object."""

  def _CreateTestEvents(self):
    """Creates events for testing.

    Returns:
      list[EventObject]: events.
    """
    test_events = []
    filetime = dfdatetime_filetime.Filetime()

    filetime.CopyFromString(u'2012-04-20 22:38:46.929596')
    values_dict = {u'Value': u'c:/Temp/evil.exe'}
    event = windows_events.WindowsRegistryEvent(
        filetime, u'MY AutoRun key', values_dict)
    event.parser = 'UNKNOWN'
    test_events.append(event)

    filetime.CopyFromString(u'2012-05-02 13:43:26.929596')
    values_dict = {u'Value': u'send all the exes to the other world'}
    event = windows_events.WindowsRegistryEvent(
        filetime, u'HKCU\\Secret\\EvilEmpire\\Malicious_key',
        values_dict)
    event.parser = 'UNKNOWN'
    test_events.append(event)

    filetime.CopyFromString(u'2012-04-20 16:44:46')
    values_dict = {u'Value': u'run all the benign stuff'}
    event = windows_events.WindowsRegistryEvent(
        filetime, u'HKCU\\Windows\\Normal', values_dict)
    event.parser = 'UNKNOWN'
    test_events.append(event)

    timemstamp = timelib.Timestamp.CopyFromString(u'2009-04-05 12:27:39')
    text_dict = {
        u'hostname': u'nomachine',
        u'text': (
            u'This is a line by someone not reading the log line properly. And '
            u'since this log line exceeds the accepted 80 chars it will be '
            u'shortened.'),
        u'username': u'johndoe'}
    event = text_events.TextEvent(timemstamp, 12, text_dict)
    event.parser = 'UNKNOWN'
    test_events.append(event)

    return test_events

  def _CreateTestEventTags(self):
    """Creates the event tags for testing.

    Returns:
      A list of event tags (instances of EventTag).
    """
    event_tags = []

    event_tag = events.EventTag()
    event_tag.store_index = 0
    event_tag.store_number = 1
    event_tag.comment = u'My comment'
    event_tags.append(event_tag)

    event_tag = events.EventTag()
    event_tag.store_index = 1
    event_tag.store_number = 1
    event_tag.AddLabel(u'Malware')
    event_tags.append(event_tag)

    event_tag = events.EventTag()
    event_tag.store_number = 1
    event_tag.store_index = 2
    event_tag.comment = u'This is interesting'
    event_tag.AddLabels([u'Malware', u'Benign'])
    event_tags.append(event_tag)

    event_tag = events.EventTag()
    event_tag.store_index = 1
    event_tag.store_number = 1
    event_tag.AddLabel(u'Interesting')
    event_tags.append(event_tag)

    return event_tags
