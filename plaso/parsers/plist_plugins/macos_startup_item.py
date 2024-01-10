# -*- coding: utf-8 -*-
"""Plist parser plugin for MacOS startup item plist files."""
from plaso.containers import events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class MacOSStartupItemEventData(events.EventData):
  """MacOS startup item event data.

  Attributes:
    description (str): a short description of the startup item.
    order_preference (str): string representing startup order preference.
    provides (list[str]): names of services provided by the startup item.
    requires (list[str]): services required prior to this startup item.
    uses (list[str]): services that should be started before this startup item.
  """

  DATA_TYPE = 'macos:startupitem:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSStartupItemEventData, self).__init__(
      data_type=self.DATA_TYPE
    )
    self.description = None
    self.order_preference = None
    self.provides = None
    self.requires = None
    self.uses = None


class MacOSStartupItemPlugin(interface.PlistPlugin):
  """Plist parser plugin for MacOS startup item plist files.
  """

  NAME = 'macos_startup_item_plist'
  DATA_FORMAT = 'MacOS startup item plist file'

  PLIST_PATH_FILTERS = frozenset([
    interface.PlistPathFilter('StartupParameters.plist')]
  )
  PLIST_KEYS = frozenset([])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, top_level=None, **unused_kwargs):
    """Extracts startup item information from the plist.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
        and other components, such as storage and dfVFS.
      top_level (Optional[dict[str, object]]): plist top-level item.
    """
    event_data = MacOSStartupItemEventData()
    event_data.description = top_level.get('Description')
    event_data.order_preference = top_level.get('OrderPreference')
    event_data.provides = top_level.get('Provides')
    event_data.requires = top_level.get('Requires')
    event_data.uses = top_level.get('Uses')
    parser_mediator.ProduceEventData(event_data)


plist.PlistParser.RegisterPlugin(MacOSStartupItemPlugin)
