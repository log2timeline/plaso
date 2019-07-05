# -*- coding: utf-8 -*-
"""Windows Registry plugin to parse the Background Activity Moderator keys."""

from __future__ import unicode_literals

# from dfdatetime import filetime as dfdatetime_filetime
# from dfdatetime import semantic_time as dfdatetime_semantic_time

# from dtfabric.runtime import data_maps as dtfabric_data_maps

from plaso.containers import events
# from plaso.containers import time_events
# from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import logger
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface
from plaso.parsers.winreg_plugins import dtfabric_plugin


class BackgroundActivityModeratorEventData(events.EventData):
  """Background Activity Moderator event data.

  Attributes:
    # TODO: Describe attributes
  """

  DATA_TYPE = 'windows:registry:bam'

  def __init__(self):
    """Initializes event data."""
    super(BackgroundActivityModeratorEventData,
          self).__init__(data_type=self.DATA_TYPE)
    # TODO: initialise attributes


class BackgroundActivityModeratorWindowsRegistryPlugin(
    dtfabric_plugin.DtFabricBaseWindowsRegistryPlugin):
  """Background Activity Moderator data Windows Registry plugin."""

  NAME = 'bam'
  DESCRIPTION = 'Parser for Background Activity Moderator Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Services\\bam'
          '\\UserSettings'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Services\\bam'
          '\\State\\UserSettings')])

  # TODO: definition
  _DEFINITION_FILE = 'bam.yaml'

  def __init__(self):
    """Initializes a Background Activity Moderator Registry plugin."""
    super(BackgroundActivityModeratorWindowsRegistryPlugin, self).__init__()

  def _ParseValue(self, registry_value):
    logger.debug('Value: {0:s}'.format(registry_value.name))

    try:
      date_time = self._ReadStructureFromByteStream(
          registry_value.data, 0, self._GetDataTypeMap('timestamp'))
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse timestamp with error: {0!s}'.format(
              exception))

    logger.debug('Timestamp: {0:d}'.format(date_time))

    return None

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
      logger.debug('Key: {0:s}'.format(sid_key.name))
      for value in sid_key.GetValues():
        if not value.name == 'Version' and not value.name == 'SequenceNumber':
          self._ParseValue(value)


winreg.WinRegistryParser.RegisterPlugin(
    BackgroundActivityModeratorWindowsRegistryPlugin)
