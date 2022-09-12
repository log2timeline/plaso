# -*- coding: utf-8 -*-
"""Plist parser plugin for MacOS TimeMachine plist files."""

import os

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class MacOSTimeMachineBackupEventData(events.EventData):
  """MacOS TimeMachine backup event data.

  Attributes:
    backup_alias (str): alias of the backup.
    destination_identifier (str): identifier of the destination volume.
  """

  DATA_TYPE = 'macos:time_machine:backup'

  def __init__(self):
    """Initializes event data."""
    super(MacOSTimeMachineBackupEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.backup_alias = None
    self.destination_identifier = None


class MacOSTimeMachinePlistPlugin(
    interface.PlistPlugin, dtfabric_helper.DtFabricHelper):
  """Plist parser plugin for MacOS TimeMachine plist files.

  Further details about the extracted fields:
    DestinationID:
      remote UUID hard disk where the backup is done.

    BackupAlias:
      structure that contains the extra information from the destinationID.

    SnapshotDates:
      list of the backup dates.
  """

  NAME = 'time_machine'
  DATA_FORMAT = 'MacOS TimeMachine plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('com.apple.TimeMachine.plist')])

  PLIST_KEYS = frozenset(['Destinations', 'RootVolumeUUID'])

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'time_machine.yaml')

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant MacOS TimeMachine entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    backup_alias_map = self._GetDataTypeMap('timemachine_backup_alias')

    destinations = match.get('Destinations', [])
    for destination in destinations:
      event_data = MacOSTimeMachineBackupEventData()
      event_data.destination_identifier = destination.get('DestinationID', None)

      backup_alias_data = destination.get('BackupAlias', None)
      if backup_alias_data:
        try:
          backup_alias = self._ReadStructureFromByteStream(
              backup_alias_data, 0, backup_alias_map)
          event_data.backup_alias = backup_alias.string

        except (ValueError, TypeError, errors.ParseError) as exception:
          parser_mediator.ProduceExtractionWarning(
              'unable to parse backup alias value with error: {0!s}'.format(
                  exception))

      snapshot_dates = destination.get('SnapshotDates', [])
      for datetime_value in snapshot_dates:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromDatetime(datetime_value)

        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_CREATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(MacOSTimeMachinePlistPlugin)
