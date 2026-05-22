"""Windows Registry plugin to Windows Explorer typed paths and URLs Registry data."""

import os
import re

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class TypedURLsTimeEventData(events.EventData):
    """Typed URLs time event data attribute container.

    Attributes:
      entry (str): typed URL.
      key_path (str): Windows Registry key path.
      last_visited_time (dfdatetime.DateTimeValues): date and time the URL was last
          visited.
    """

    DATA_TYPE = "windows:registry:typedurlstime"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.entry = None
        self.key_path = None
        self.last_visited_time = None


class TypedURLsTimePlugin(
    interface.WindowsRegistryPlugin, dtfabric_helper.DtFabricHelper
):
    """Windows Registry plugin to parse TypedURLsTime keys."""

    NAME = "windows_typed_urls_time"
    DATA_FORMAT = "Windows Explorer typed URLs time Registry data"

    CONTEXT_KEYS = {
        "typed_urls_key": (
            "HKEY_CURRENT_USER\\Software\\Microsoft\\Internet Explorer\\TypedURLs"
        )
    }

    FILTERS = frozenset(
        [
            interface.WindowsRegistryKeyPathFilter(
                "HKEY_CURRENT_USER\\Software\\Microsoft\\Internet Explorer\\"
                "TypedURLsTime"
            ),
        ]
    )

    _DEFINITION_FILE = os.path.join(os.path.dirname(__file__), "filetime.yaml")

    _RE_VALUE_NAME = re.compile(r"^url[0-9]+$", re.I)

    def _ParseFiletime(self, byte_stream):
        """Parses a FILETIME date and time value from a byte stream.

        Args:
          byte_stream (bytes): byte stream.

        Returns:
          dfdatetime.DateTimeValues: a FILETIME date and time values or a semantic
              date and time values if the FILETIME date and time value is not set.

        Raises:
          ParseError: if the FILETIME could not be parsed.
        """
        filetime_map = self._GetDataTypeMap("filetime")

        try:
            filetime = self._ReadStructureFromByteStream(byte_stream, 0, filetime_map)
        except (ValueError, errors.ParseError) as exception:
            raise errors.ParseError(
                f"Unable to parse FILETIME value with error: {exception!s}"
            )

        if filetime == 0:
            return dfdatetime_semantic_time.NotSet()

        try:
            return dfdatetime_filetime.Filetime(timestamp=filetime)
        except ValueError:
            raise errors.ParseError(f"Invalid FILETIME value: 0x{filetime:08x}")

    def ExtractEvents(
        self, parser_mediator, registry_key, typed_urls_key=None, **kwargs
    ):
        """Extracts events from a Windows Registry key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
          typed_urls_key (Optional[dfwinreg.WinRegistryKey]): TypedURLs context Windows
              Registry key.
        """
        for registry_value in registry_key.GetValues():
            value_name = registry_value.name

            # Ignore any value not in the form: 'url[0-9]+'.
            if not value_name or not self._RE_VALUE_NAME.search(value_name):
                continue

            # Ignore any value that is empty or that does not contain a binary data.
            if not registry_value.data or not registry_value.DataIsBinaryData():
                continue

            typed_urls_value = typed_urls_key.GetValueByName(value_name)

            if (
                typed_urls_value
                and typed_urls_value.data
                and typed_urls_value.DataIsString()
            ):
                value_string = typed_urls_value.GetDataAsObject()
                entry_string = f"{value_name:s}: {value_string:s}"
            else:
                entry_string = value_name

            date_time = self._ParseFiletime(registry_value.data)

            event_data = TypedURLsTimeEventData()
            event_data.entry = entry_string
            event_data.key_path = registry_key.path
            event_data.last_visited_time = date_time

            parser_mediator.ProduceEventData(event_data)

        self._ProduceDefaultWindowsRegistryEvent(parser_mediator, registry_key)


winreg_parser.WinRegistryParser.RegisterPlugin(TypedURLsTimePlugin)
