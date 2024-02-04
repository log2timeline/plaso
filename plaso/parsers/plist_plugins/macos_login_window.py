# -*- coding: utf-8 -*-
"""Plist parser plugin for MacOS login window plist files."""

from plaso.containers import events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class MacOSLoginWindowAutoLaunchApplicationEventData(events.EventData):
  """MacOS autolaunch application event data.

  Attributes:
    hidden (bool): if true, the item is hidden from the "Users & Groups" GUI.
    path (str): A URL or path string to the item's location.
  """

  DATA_TYPE = 'macos:login_window:auto_launched_application'

  def __init__(self):
    """Initializes event data."""
    super(MacOSLoginWindowAutoLaunchApplicationEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.hidden = None
    self.path = None


class MacOSLoginWindowHookEventData(events.EventData):
  """MacOS login window hook event data.

  Attributes:
    path (str): path to script invoked on login.
    hook_type (str): either "login" or "logout".
  """

  DATA_TYPE = 'macos:login_window:hook'

  def __init__(self):
    """Initializes event data."""
    super(MacOSLoginWindowHookEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.path = None
    self.hook_type = None


class MacOSLoginWindowPlugin(interface.PlistPlugin):
  """Plist parser plugin for MacOS login window plist files."""

  NAME = 'macos_login_window_plist'
  DATA_FORMAT = 'MacOS login window plist file'

  PLIST_PATH_FILTERS = frozenset([
    interface.PlistPathFilter('loginwindow.plist'),
    interface.PlistPathFilter('com.apple.loginwindow.plist')])

  PLIST_KEYS = frozenset([])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, top_level=None, **unused_kwargs):
    """Extracts login window information from the plist.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      top_level (Optional[dict[str, object]]): plist top-level item.
    """
    for app_dict in top_level.get('AutoLaunchedApplicationDictionary', []):
      event_data = MacOSLoginWindowAutoLaunchApplicationEventData()
      event_data.hidden = app_dict.get('Hide')
      event_data.path = app_dict.get('Path')
      parser_mediator.ProduceEventData(event_data)

    login_hook = top_level.get('LoginHook')
    if login_hook is not None:
      event_data = MacOSLoginWindowHookEventData()
      event_data.path = login_hook
      event_data.hook_type = 'login'
      parser_mediator.ProduceEventData(event_data)

    logout_hook = top_level.get('LogoutHook')
    if logout_hook is not None:
      event_data = MacOSLoginWindowHookEventData()
      event_data.path = logout_hook
      event_data.hook_type = 'logout'
      parser_mediator.ProduceEventData(event_data)


plist.PlistParser.RegisterPlugin(MacOSLoginWindowPlugin)
