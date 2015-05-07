# -*- coding: utf-8 -*-
"""This file contains a TimeMachine plist plugin in Plaso."""

import construct

from plaso.events import plist_event
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
      parser_mediator: A parser mediator object (instance of ParserMediator).
      match: Optional dictionary containing keys extracted from PLIST_KEYS.
             The default is None.
    """
    if u'Destinations' not in match:
      return

    root = u'/Destinations'
    key = u'item/SnapshotDates'

    # For each TimeMachine devices.
    for destination in match[u'Destinations']:
      hd_uuid = destination.get(u'DestinationID', None)
      if not hd_uuid:
        hd_uuid = u'Unknown device'

      alias = destination.get(u'BackupAlias', u'<ALIAS>')
      try:
        alias = self.TM_BACKUP_ALIAS.parse(alias).value
      except construct.FieldError:
        alias = u'Unknown alias'

      # For each Backup.
      for timestamp in destination.get(u'SnapshotDates', []):
        description = u'TimeMachine Backup in {0:s} ({1:s})'.format(
            alias, hd_uuid)
        event_object = plist_event.PlistEvent(root, key, timestamp, description)
        parser_mediator.ProduceEvent(event_object)


plist.PlistParser.RegisterPlugin(TimeMachinePlugin)
