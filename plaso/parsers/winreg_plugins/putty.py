"""This file contains the PuTTY Windows Registry plugins."""

import urllib.parse

from plaso.containers import events
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class PuTTYSessionEventData(events.EventData):
    """PuTTY saved session event data attribute container.

    Attributes:
      remote_hostname (str): host name or IP address of the remote host.
      key_path (str): Windows Registry key path.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and
          time.
      port_number (int): port number of the remote host.
      protocol (str): connection protocol, such as "ssh", "telnet" or "serial".
      public_key_file (str): path of the private key file used for
          authentication.
      session_name (str): name of the saved session.
      username (str): user name used to log in to the remote host.
    """

    DATA_TYPE = "windows:registry:putty:session"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.remote_hostname = None
        self.key_path = None
        self.last_written_time = None
        self.port_number = None
        self.protocol = None
        self.public_key_file = None
        self.session_name = None
        self.username = None


class PuTTYSSHHostKeysEventData(events.EventData):
    """PuTTY SSH host keys event data attribute container.

    Attributes:
      entries (str): SSH host key entries, in the form "key_type@port:host".
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

    def _GetStringValueFromKey(self, registry_key, value_name):
        """Retrieves a string value from the Windows Registry key.

        Args:
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
          value_name (str): name of the value to retrieve.

        Returns:
          str: value string or None if not available or empty.
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
        """Extracts events from a PuTTY saved sessions Windows Registry key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
        """
        for subkey in registry_key.GetSubkeys():
            port_number = None
            registry_value = subkey.GetValueByName("PortNumber")
            if registry_value and registry_value.DataIsInteger():
                port_number = registry_value.GetDataAsObject()

            event_data = PuTTYSessionEventData()
            event_data.remote_hostname = self._GetStringValueFromKey(subkey, "HostName")
            event_data.key_path = subkey.path
            event_data.last_written_time = subkey.last_written_time
            event_data.port_number = port_number
            event_data.protocol = self._GetStringValueFromKey(subkey, "Protocol")
            event_data.public_key_file = self._GetStringValueFromKey(
                subkey, "PublicKeyFile"
            )
            # PuTTY stores the session name with special characters, such as
            # space, percent-encoded, for example "Default%20Settings".
            event_data.session_name = urllib.parse.unquote(subkey.name)
            event_data.username = self._GetStringValueFromKey(subkey, "UserName")

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
        # The value name is in the form "key_type@port:host", for example
        # "ssh-ed25519@22:192.168.1.10". The value data contains the host key
        # itself and is not included.
        entries = [
            registry_value.name
            for registry_value in registry_key.GetValues()
            if registry_value.name
        ]

        event_data = PuTTYSSHHostKeysEventData()
        event_data.entries = " ".join(entries) or None
        event_data.key_path = registry_key.path
        event_data.last_written_time = registry_key.last_written_time

        parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugin(PuTTYSessionsPlugin)
winreg_parser.WinRegistryParser.RegisterPlugin(PuTTYSSHHostKeysPlugin)
