# -*- coding: utf-8 -*-
"""TimeMachine plist plugin."""

from __future__ import unicode_literals

import codecs

import construct

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class TimeMachinePlugin(interface.PlistPlugin):
  """Basic plugin to extract time machine hard disk and the backups.

  Further details about the extracted fields:
    DestinationID:
      remote UUID hard disk where the backup is done.

    BackupAlias:
      structure that contains the extra information from the destinationID.

    SnapshotDates:
      list of the backup dates.
  """

  NAME = 'time_machine'
  DESCRIPTION = 'Parser for TimeMachine plist files.'

  PLIST_PATH = 'com.apple.TimeMachine.plist'
  PLIST_KEYS = frozenset(['Destinations', 'RootVolumeUUID'])

  TM_BACKUP_ALIAS = construct.Struct(
      'tm_backup_alias',
      construct.Padding(10),
      construct.PascalString(
          'value', length_field=construct.UBInt8('length')))

  # pylint: disable=arguments-differ
  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant TimeMachine entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    destinations = match.get('Destinations', [])
    for destination in destinations:
      destination_identifier = (
          destination.get('DestinationID', None) or 'Unknown device')

      alias = destination.get('BackupAlias', '<ALIAS>')
      try:
        alias = self.TM_BACKUP_ALIAS.parse(alias).value
        alias = codecs.decode(alias, 'utf-8')
      except construct.FieldError:
        alias = 'Unknown alias'

      event_data = plist_event.PlistTimeEventData()
      event_data.desc = 'TimeMachine Backup in {0:s} ({1:s})'.format(
          alias, destination_identifier)
      event_data.key = 'item/SnapshotDates'
      event_data.root = '/Destinations'

      snapshot_dates = destination.get('SnapshotDates', [])
      for datetime_value in snapshot_dates:
        event = time_events.PythonDatetimeEvent(
            datetime_value, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(TimeMachinePlugin)
