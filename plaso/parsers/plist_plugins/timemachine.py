# -*- coding: utf-8 -*-
"""This file contains a TimeMachine plist plugin in Plaso."""

import construct

from plaso.events import plist_event
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class TimeMachinePlugin(interface.PlistPlugin):
  """Basic plugin to extract time machine hardisk and the backups."""

  NAME = 'plist_timemachine'
  DESCRIPTION = u'Parser for TimeMachine plist files.'

  PLIST_PATH = 'com.apple.TimeMachine.plist'
  PLIST_KEYS = frozenset(['Destinations', 'RootVolumeUUID'])

  # Generated events:
  # DestinationID: remote UUID hard disk where the backup is done.
  # BackupAlias: structure that contains the extra information from the
  #              destinationID.
  # SnapshotDates: list of the backup dates.

  TM_BACKUP_ALIAS = construct.Struct(
      'tm_backup_alias',
      construct.Padding(10),
      construct.PascalString('value', length_field=construct.UBInt8('length')))

  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant TimeMachine entries.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      match: Optional dictionary containing keys extracted from PLIST_KEYS.
             The default is None.
    """
    root = '/Destinations'
    key = 'item/SnapshotDates'

    # For each TimeMachine devices.
    for destination in match['Destinations']:
      hd_uuid = destination['DestinationID']
      if not hd_uuid:
        hd_uuid = u'Unknown device'
      alias = destination['BackupAlias']
      try:
        alias = self.TM_BACKUP_ALIAS.parse(alias).value
      except construct.FieldError:
        alias = u'Unknown alias'
      # For each Backup.
      for timestamp in destination['SnapshotDates']:
        description = u'TimeMachine Backup in {0:s} ({1:s})'.format(
            alias, hd_uuid)
        event_object = plist_event.PlistEvent(root, key, timestamp, description)
        parser_mediator.ProduceEvent(event_object)


plist.PlistParser.RegisterPlugin(TimeMachinePlugin)
