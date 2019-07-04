# -*- coding: utf-8 -*-
"""Windows Registry plugin to parse the Background Activity Moderator keys."""

from __future__ import unicode_literals

from plaso.containers import events
from plaso.parsers import winreg
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

  # TODO: FILTERS =

  # TODO: definition
  _DEFINITION_FILE = 'bam.yaml'

  def __init__(self):
    """Initializes a Background Activity Moderator Registry plugin."""
    super(BackgroundActivityModeratorWindowsRegistryPlugin, self).__init__()

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.

    Raises:
      ParseError: if the value data could not be parsed.
    """


winreg.WinRegistryParser.RegisterPlugin(
    BackgroundActivityModeratorWindowsRegistryPlugin)
