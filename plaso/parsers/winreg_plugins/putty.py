"""This file contains the PuTTY Windows Registry plugins."""

from plaso.containers import events
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class PuTTYSessionEventData(events.EventData):
    """PuTTY session event data attribute container.

    Attributes:
      hostname (str): host name or IP address, provided by the HostName value.
      key_path (str): Windows Registry key path.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and
          time.
      port_number (int): port number, provided by the PortNumber value.
      protocol (str): protocol, such as "ssh" or "telnet", provided by
          the Protocol value.
      username (str): username, provided by the UserName value.
    """

    DATA_TYPE = "windows:registry:putty:session"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.hostname = None
        self.key_path = None
        self.last_written_time = None
        self.port_number = None
        self.protocol = None
        self.username = None


class PuTTYSSHHostKeysEventData(events.EventData):
    """PuTTY SSH host keys event data attribute container.

    Attributes:
      entries (str): names of the SSH host key values, which are formatted as
          "{key type}@{port number}:{host name}".
      key_path (str): Windows Registry key path.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and
          time.
    """

    DATA_TYPE = "windows:registry:putty:ssh_host_keys"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.entries = None
        self.key_path = None
        self.last_written_time = None


class PuTTYSessionsPlugin(interface.WindowsRegistryPlugin):
    """Windows Registry plugin for PuTTY sessions keys."""

    NAME = "putty_sessions"
    DATA_FORMAT = "PuTTY sessions Registry data"

    FILTERS = frozenset(
        [
            interface.WindowsRegistryKeyPathFilter(
                "HKEY_CURRENT_USER\\Software\\SimonTatham\\PuTTY\\Sessions"
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
        """Extracts events from a PuTTY sessions Windows Registry key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
        """
        for subkey in registry_key.GetSubkeys():
            event_data = PuTTYSessionEventData()
            event_data.hostname = self._GetStringValue(subkey, "HostName")
            event_data.key_path = subkey.path
            event_data.last_written_time = subkey.last_written_time
            event_data.port_number = self._GetIntegerValue(subkey, "PortNumber")
            event_data.protocol = self._GetStringValue(subkey, "Protocol")
            event_data.username = self._GetStringValue(subkey, "UserName")

            parser_mediator.ProduceEventData(event_data)


class PuTTYSSHHostKeysPlugin(interface.WindowsRegistryPlugin):
    """Windows Registry plugin for PuTTY SSH host keys keys."""

    NAME = "putty_ssh_host_keys"
    DATA_FORMAT = "PuTTY SSH host keys Registry data"

    FILTERS = frozenset(
        [
            interface.WindowsRegistryKeyPathFilter(
                "HKEY_CURRENT_USER\\Software\\SimonTatham\\PuTTY\\SshHostKeys"
            )
        ]
    )

    def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
        """Extracts events from a PuTTY SSH host keys Windows Registry key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
        """
        entries = []
        for registry_value in registry_key.GetValues():
            # Ignore the default value.
            if not registry_value.name:
                continue

            # Ignore any value that is empty or that does not contain a string.
            if not registry_value.data or not registry_value.DataIsString():
                continue

            entries.append(registry_value.name)

        event_data = PuTTYSSHHostKeysEventData()
        event_data.entries = " ".join(entries) or None
        event_data.key_path = registry_key.path
        event_data.last_written_time = registry_key.last_written_time

        parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugins(
    [PuTTYSessionsPlugin, PuTTYSSHHostKeysPlugin]
)
