# -*- coding: utf-8 -*-
"""TimeMachine plist plugin."""

from dfdatetime import posix_time as dfdatetime_posix_time

import construct

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class TimeMachinePlugin(interface.PlistPlugin):
  """Basic plugin to extract time machine hardisk and the backups.

  Further details about the extracted fields:
    DestinationID:
      remote UUID hard disk where the backup is done.

    BackupAlias:
      structure that contains the extra information from the destinationID.

    SnapshotDates:
      list of the backup dates.
  """

  NAME = u'time_machine'
  DESCRIPTION = u'Parser for TimeMachine plist files.'

  PLIST_PATH = u'com.apple.TimeMachine.plist'
  PLIST_KEYS = frozenset([u'Destinations', u'RootVolumeUUID'])

  TM_BACKUP_ALIAS = construct.Struct(
      u'tm_backup_alias',
      construct.Padding(10),
      construct.PascalString(
          u'value', length_field=construct.UBInt8(u'length')))

  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant TimeMachine entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    destinations = match.get(u'Destinations', [])
    for destination in destinations:
      destination_identifier = (
          destination.get(u'DestinationID', None) or u'Unknown device')

      alias = destination.get(u'BackupAlias', u'<ALIAS>')
      try:
        alias = self.TM_BACKUP_ALIAS.parse(alias).value
      except construct.FieldError:
        alias = u'Unknown alias'

      event_data = plist_event.PlistTimeEventData()
      event_data.desc = u'TimeMachine Backup in {0:s} ({1:s})'.format(
          alias, destination_identifier)
      event_data.key = u'item/SnapshotDates'
      event_data.root = u'/Destinations'

      snapshot_dates = destination.get(u'SnapshotDates', [])
      for datetime_value in snapshot_dates:
        timestamp = timelib.Timestamp.FromPythonDatetime(datetime_value)
        date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
            timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(TimeMachinePlugin)
