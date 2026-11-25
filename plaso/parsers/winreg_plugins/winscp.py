"""This file contains the WinSCP sessions Windows Registry plugin."""

from plaso.containers import events
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class WinSCPSessionEventData(events.EventData):
    """WinSCP session event data attribute container.

    Attributes:
      hostname (str): host name or IP address, provided by the HostName value.
      key_path (str): Windows Registry key path.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and
          time.
      port_number (int): port number, provided by the PortNumber value.
      username (str): username, provided by the UserName value.
    """

    DATA_TYPE = "windows:registry:winscp:session"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.hostname = None
        self.key_path = None
        self.last_written_time = None
        self.port_number = None
        self.username = None


class WinSCPSessionsPlugin(interface.WindowsRegistryPlugin):
    """Windows Registry plugin for WinSCP sessions keys."""

    NAME = "winscp_sessions"
    DATA_FORMAT = "WinSCP sessions Registry data"

    FILTERS = frozenset(
        [
            interface.WindowsRegistryKeyPathFilter(
                "HKEY_CURRENT_USER\\Software\\Martin Prikryl\\WinSCP 2\\Sessions"
            )
        ]
    )

    def _GetIntegerValue(self, registry_key, value_name):
        """Retrieves an integer value from a Windows Registry key.

        Args:
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
          value_name (str): name of the value.

        Returns:
          int: value data or None if the value is not available or does not
              contain an integer.
        """
        registry_value = registry_key.GetValueByName(value_name)
        if not registry_value or not registry_value.DataIsInteger():
            return None

        return registry_value.GetDataAsObject()

    def _GetStringValue(self, registry_key, value_name):
        """Retrieves a string value from a Windows Registry key.

        Args:
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
          value_name (str): name of the value.

        Returns:
          str: value data or None if the value is not available, is empty or
              does not contain a string.
        """
        registry_value = registry_key.GetValueByName(value_name)
        if (
            not registry_value
            or not registry_value.data
            or not registry_value.DataIsString()
        ):
            return None

        return registry_value.GetDataAsObject() or None

    def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
        """Extracts events from a WinSCP sessions Windows Registry key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
        """
        for subkey in registry_key.GetSubkeys():
            event_data = WinSCPSessionEventData()
            event_data.hostname = self._GetStringValue(subkey, "HostName")
            event_data.key_path = subkey.path
            event_data.last_written_time = subkey.last_written_time
            event_data.port_number = self._GetIntegerValue(subkey, "PortNumber")
            event_data.username = self._GetStringValue(subkey, "UserName")

            parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugin(WinSCPSessionsPlugin)
