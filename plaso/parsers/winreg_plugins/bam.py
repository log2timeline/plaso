# -*- coding: utf-8 -*-
"""Windows Registry plugin to parse the Background Activity Moderator keys."""

import os

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class BackgroundActivityModeratorEventData(events.EventData):
  """Background Activity Moderator event data.

  Attributes:
    last_run_time (dfdatetime.DateTimeValues): executable (binary) last run
        date and time.
    path (str): path of the executable (binary).
    user_identifier (str): user identifier (Windows NT SID).
  """

  DATA_TYPE = 'windows:registry:bam'

  def __init__(self):
    """Initializes event data."""
    super(BackgroundActivityModeratorEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.last_run_time = None
    self.path = None
    self.user_identifier = None


class BackgroundActivityModeratorWindowsRegistryPlugin(
    interface.WindowsRegistryPlugin, dtfabric_helper.DtFabricHelper):
  """Background Activity Moderator data Windows Registry plugin."""

  NAME = 'bam'
  DATA_FORMAT = 'Background Activity Moderator (BAM) Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Services\\bam'
          '\\UserSettings'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Services\\bam'
          '\\State\\UserSettings')])

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'filetime.yaml')

  def _ParseValue(self, registry_value):
    """Parses the registry value.

    Args:
      registry_value (bytes): value data.

    Returns:
      int: timestamp.

    Raises:
      ParseError: if the value data could not be parsed.
    """
    try:
      timestamp = self._ReadStructureFromByteStream(
          registry_value, 0, self._GetDataTypeMap('filetime'))
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse timestamp with error: {0!s}'.format(
              exception))

    return timestamp

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.

    Raises:
      ParseError: if the value data could not be parsed.
    """
    for sid_key in registry_key.GetSubkeys():
      for value in sid_key.GetValues():
        if value.name in ('SequenceNumber', 'Version'):
          continue

        event_data = BackgroundActivityModeratorEventData()
        event_data.path = value.name
        event_data.user_identifier = sid_key.name

        timestamp = self._ParseValue(value.data)
        if timestamp:
          event_data.last_run_time = dfdatetime_filetime.Filetime(
              timestamp=timestamp)

        parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugin(
    BackgroundActivityModeratorWindowsRegistryPlugin)
