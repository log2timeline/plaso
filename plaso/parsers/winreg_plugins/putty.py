"""This file contains the PuTTY Windows Registry plugin."""

import urllib.parse

from plaso.containers import events
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class PuTTYSessionEventData(events.EventData):
    """PuTTY saved session event data attribute container.

    Attributes:
      key_path (str): Windows Registry key path.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and
          time.
      port_number (int): port number of the remote host.
      protocol (str): connection protocol, such as "ssh", "telnet" or "serial".
      public_key_file (str): path of the private key file used for
          authentication.
      remote_hostname (str): host name or IP address of the remote host.
      session_name (str): name of the saved session.
      username (str): user name used to log in to the remote host.
    """

    DATA_TYPE = "windows:registry:putty:session"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.key_path = None
        self.last_written_time = None
        self.port_number = None
        self.protocol = None
        self.public_key_file = None
        self.remote_hostname = None
        self.session_name = None
        self.username = None


class PuTTYSessionsPlugin(interface.WindowsRegistryPlugin):
    """Windows Registry plugin for PuTTY saved sessions keys."""

    NAME = "putty_sessions"
    DATA_FORMAT = "PuTTY saved sessions Registry data"

    FILTERS = frozenset(
        [
            interface.WindowsRegistryKeyPathFilter(
                "HKEY_CURRENT_USER\\Software\\SimonTatham\\PuTTY\\Sessions"
            )
        ]
    )

    def _GetIntegerValueFromKey(self, parser_mediator, registry_key, value_name):
        """Retrieves an integer value from the Windows Registry key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
          value_name (str): name of the value to retrieve.

        Returns:
          tuple[int, bool]: value integer or None if not available, and True if
              the value is not an integer.
        """
        registry_value = registry_key.GetValueByName(value_name)
        if not registry_value:
            return None, False

        if not registry_value.DataIsInteger():
            parser_mediator.ProduceWarning(
                f"unsupported data type of value: {value_name:s} in key: "
                f"{registry_key.path:s}, expected integer"
            )
            return None, True

        return registry_value.GetDataAsObject(), False

    def _GetStringValueFromKey(self, parser_mediator, registry_key, value_name):
        """Retrieves a string value from the Windows Registry key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
          value_name (str): name of the value to retrieve.

        Returns:
          tuple[str, bool]: value string or None if not available or empty, and
              True if the value is not a string.
        """
        registry_value = registry_key.GetValueByName(value_name)
        if not registry_value:
            return None, False

        if not registry_value.DataIsString():
            parser_mediator.ProduceWarning(
                f"unsupported data type of value: {value_name:s} in key: "
                f"{registry_key.path:s}, expected string"
            )
            return None, True

        # PuTTY stores values that are not set as an empty string.
        return registry_value.GetDataAsObject() or None, False

    def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
        """Extracts events from a PuTTY saved sessions Windows Registry key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
        """
        for subkey in registry_key.GetSubkeys():
            port_number, port_number_corrupted = self._GetIntegerValueFromKey(
                parser_mediator, subkey, "PortNumber"
            )
            protocol, protocol_corrupted = self._GetStringValueFromKey(
                parser_mediator, subkey, "Protocol"
            )
            public_key_file, public_key_file_corrupted = self._GetStringValueFromKey(
                parser_mediator, subkey, "PublicKeyFile"
            )
            remote_hostname, remote_hostname_corrupted = self._GetStringValueFromKey(
                parser_mediator, subkey, "HostName"
            )
            username, username_corrupted = self._GetStringValueFromKey(
                parser_mediator, subkey, "UserName"
            )

            event_data = PuTTYSessionEventData()
            event_data.key_path = subkey.path
            event_data.last_written_time = subkey.last_written_time
            event_data.port_number = port_number
            event_data.protocol = protocol
            event_data.public_key_file = public_key_file
            event_data.remote_hostname = remote_hostname
            # PuTTY stores the session name with special characters, such as
            # space, percent-encoded, for example "Default%20Settings".
            event_data.session_name = urllib.parse.unquote(subkey.name)
            event_data.username = username

            corrupted = (
                port_number_corrupted
                or protocol_corrupted
                or public_key_file_corrupted
                or remote_hostname_corrupted
                or username_corrupted
            )
            parser_mediator.ProduceEventData(event_data, corrupted=corrupted)


winreg_parser.WinRegistryParser.RegisterPlugin(PuTTYSessionsPlugin)
