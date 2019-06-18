# -*- coding: utf-8 -*-
"""Storage related functions and classes for testing."""

from __future__ import unicode_literals

from plaso.containers import events
from plaso.lib import definitions
from plaso.lib import timelib

from tests import test_lib as shared_test_lib


class StorageTestCase(shared_test_lib.BaseTestCase):
  """The unit test case for a storage object."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'windows:registry:key_value',
       'key_path': 'MY AutoRun key',
       'parser': 'UNKNOWN',
       'timestamp': timelib.Timestamp.CopyFromString(
           '2012-04-20 22:38:46.929596'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN,
       'values': 'Value: c:/Temp/evil.exe'},
      {'data_type': 'windows:registry:key_value',
       'key_path': 'HKEY_CURRENT_USER\\Secret\\EvilEmpire\\Malicious_key',
       'parser': 'UNKNOWN',
       'timestamp': timelib.Timestamp.CopyFromString(
           '2012-04-20 23:56:46.929596'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN,
       'values': 'Value: send all the exes to the other world'},
      {'data_type': 'windows:registry:key_value',
       'key_path': 'HKEY_CURRENT_USER\\Windows\\Normal',
       'parser': 'UNKNOWN',
       'timestamp': timelib.Timestamp.CopyFromString('2012-04-20 16:44:46'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN,
       'values': 'Value: run all the benign stuff'},
      {'data_type': 'text:entry',
       'hostname': 'nomachine',
       'offset': 12,
       'parser': 'UNKNOWN',
       'text': (
           'This is a line by someone not reading the log line properly. And '
           'since this log line exceeds the accepted 80 chars it will be '
           'shortened.'),
       'timestamp': timelib.Timestamp.CopyFromString('2009-04-05 12:27:39'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN,
       'username': 'johndoe'}]

  def _CreateTestEventTags(self, test_events):
    """Creates the event tags for testing.

    Args:
      list[EventObject]: events to tag.

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
