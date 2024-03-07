# -*- coding: utf-8 -*-
"""Plist parser plugin for Mac OS login window plist files."""

from plaso.containers import events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class MacOSLoginWindowEventData(events.EventData):
  """Mac OS login window event data.

  Also see:
  * https://developer.apple.com/documentation/devicemanagement/loginwindow
  * https://developer.apple.com/documentation/devicemanagement/
    loginwindowscripts

  Attributes:
    login_hook (str): path of the script to run during login.
    logout_hook (str): path of the script to run during logout.
  """

  DATA_TYPE = 'macos:login_window:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSLoginWindowEventData, self).__init__(data_type=self.DATA_TYPE)
    self.login_hook = None
    self.logout_hook = None


class MacOSLoginWindowManagedLoginItemEventData(events.EventData):
  """Mac OS login window managed login item event data.

  Also see:
  * https://developer.apple.com/documentation/devicemanagement/
    loginitemsmanageditems/loginitem

  Attributes:
    is_hidden (bool): True if the item should is not shown in the "Users &
        Groups" items list.
    path (str): URL or path of the location of the item.
  """

  DATA_TYPE = 'macos:login_window:managed_login_item'

  def __init__(self):
    """Initializes event data."""
    super(MacOSLoginWindowManagedLoginItemEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.is_hidden = None
    self.path = None


class MacOSLoginWindowPlugin(interface.PlistPlugin):
  """Plist parser plugin for Mac OS login window plist files."""

  NAME = 'macos_login_window_plist'
  DATA_FORMAT = 'Mac OS login window plist file'

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
    for item in top_level.get('AutoLaunchedApplicationDictionary', []):
      event_data = MacOSLoginWindowManagedLoginItemEventData()
      event_data.is_hidden = item.get('Hide')
      event_data.path = item.get('Path')
      parser_mediator.ProduceEventData(event_data)

    event_data = MacOSLoginWindowEventData()
    event_data.login_hook = top_level.get('LoginHook')
    event_data.logout_hook = top_level.get('LogoutHook')
    parser_mediator.ProduceEventData(event_data)


plist.PlistParser.RegisterPlugin(MacOSLoginWindowPlugin)
