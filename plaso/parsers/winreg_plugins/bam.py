# -*- coding: utf-8 -*-
"""Windows Registry plugin to parse the Background Activity Moderator keys."""

import os

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class BackgroundActivityModeratorEventData(events.EventData):
  """Background Activity Moderator event data.

  Attributes:
    binary_path (str): binary executed.
    user_sid (str): user SID associated with entry.
  """

  DATA_TYPE = 'windows:registry:bam'

  def __init__(self):
    """Initializes event data."""
    super(
        BackgroundActivityModeratorEventData,
        self).__init__(data_type=self.DATA_TYPE)
    self.binary_path = None
    self.user_sid = None


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
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.

    Raises:
      ParseError: if the value data could not be parsed.
    """
    sid_keys = registry_key.GetSubkeys()
    if not sid_keys:
      return

    for sid_key in sid_keys:
      for value in sid_key.GetValues():
        if not value.name == 'Version' and not value.name == 'SequenceNumber':
          timestamp = self._ParseValue(value.data)

          if timestamp:
            event_data = BackgroundActivityModeratorEventData()
            event_data.binary_path = value.name
            event_data.user_sid = sid_key.name

            date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)

            event = time_events.DateTimeValuesEvent(
                date_time, definitions.TIME_DESCRIPTION_LAST_RUN)
            parser_mediator.ProduceEventWithEventData(event, event_data)


winreg_parser.WinRegistryParser.RegisterPlugin(
    BackgroundActivityModeratorWindowsRegistryPlugin)
