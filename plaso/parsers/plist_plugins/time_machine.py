# -*- coding: utf-8 -*-
"""Plist parser plugin for MacOS TimeMachine plist files."""

import os

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class MacOSTimeMachineBackupEventData(events.EventData):
  """MacOS TimeMachine backup event data.

  Attributes:
    backup_alias (str): alias of the backup.
    destination_identifier (str): identifier of the destination volume.
    snapshot_times (list[dfdatetime.DateTimeValues]): dates and times of
        the creation of backup snaphots.
  """

  DATA_TYPE = 'macos:time_machine:backup'

  def __init__(self):
    """Initializes event data."""
    super(MacOSTimeMachineBackupEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.backup_alias = None
    self.destination_identifier = None
    self.snapshot_times = None


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

  def __init__(self):
    """Initializes a plist parser plugin."""
    super(MacOSTimeMachinePlistPlugin, self).__init__()
    self._backup_alias_map = self._GetDataTypeMap('timemachine_backup_alias')

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant MacOS TimeMachine entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    for destination in match.get('Destinations', []):
      backup_alias_string = None
      snapshot_times = []

      backup_alias_data = destination.get('BackupAlias', None)
      if backup_alias_data:
        try:
          backup_alias = self._ReadStructureFromByteStream(
              backup_alias_data, 0, self._backup_alias_map)
          backup_alias_string = backup_alias.string

        except (ValueError, TypeError, errors.ParseError) as exception:
          parser_mediator.ProduceExtractionWarning(
              'unable to parse backup alias value with error: {0!s}'.format(
                  exception))

      for datetime_value in destination.get('SnapshotDates', []):
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromDatetime(datetime_value)
        snapshot_times.append(date_time)

      event_data = MacOSTimeMachineBackupEventData()
      event_data.backup_alias = backup_alias_string
      event_data.destination_identifier = destination.get('DestinationID', None)
      event_data.snapshot_times = snapshot_times or None

      parser_mediator.ProduceEventData(event_data)


plist.PlistParser.RegisterPlugin(MacOSTimeMachinePlistPlugin)
