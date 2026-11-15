"""Windows Registry plugin to parse Windows Explorer FeatureUsage Registry data.

The FeatureUsage subkeys contain per application, or per taskbar (tray) button,
counters of taskbar interactions, on Windows 10 version 1903 and later.

Also see:
  https://www.group-ib.com/blog/featureusage/
"""

from dfwinreg import errors as dfwinreg_errors

from plaso.containers import events
from plaso.helpers.windows import known_folders
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class FeatureUsageEventData(events.EventData):
    """Windows Explorer FeatureUsage event data attribute container.

    Attributes:
      entries (list[str]): applications or taskbar (tray) buttons with their usage
          counts.
      key_path (str): Windows Registry key path.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and
          time.
    """

    DATA_TYPE = "windows:registry:explorer:feature_usage"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.entries = None
        self.key_path = None
        self.last_written_time = None


class FeatureUsageWindowsRegistryKeyPathFilter(interface.WindowsRegistryKeyPathFilter):
    """FeatureUsage Windows Registry key path filter."""

    _KEY_PATH = (
        "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\"
        "Explorer\\FeatureUsage"
    )

    def __init__(self, subkey_name):
        """Initializes Windows Registry key filter.

        Args:
          subkey_name (str): name of the FeatureUsage subkey.
        """
        super().__init__(f"{self._KEY_PATH:s}\\{subkey_name:s}")


class FeatureUsagePlugin(interface.WindowsRegistryPlugin):
    """Windows Registry plugin to parse the FeatureUsage subkeys."""

    NAME = "explorer_feature_usage"
    DATA_FORMAT = "Windows Explorer feature usage Registry data"

    FILTERS = frozenset(
        [
            FeatureUsageWindowsRegistryKeyPathFilter("AppBadgeUpdated"),
            FeatureUsageWindowsRegistryKeyPathFilter("AppLaunch"),
            FeatureUsageWindowsRegistryKeyPathFilter("AppSwitched"),
            FeatureUsageWindowsRegistryKeyPathFilter("ShowJumpView"),
            FeatureUsageWindowsRegistryKeyPathFilter("TrayButtonClicked"),
        ]
    )

    def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
        """Extracts events from a Windows Registry key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
        """
        entries = []
        for registry_value in registry_key.GetValues():
            value_name = registry_value.name

            # Ignore the default value.
            if not value_name:
                continue

            if not registry_value.DataIsInteger():
                parser_mediator.ProduceWarning(
                    f"unsupported value: {value_name:s} data type: "
                    f"{registry_value.data_type_string:s}"
                )
                continue

            try:
                usage_count = registry_value.GetDataAsObject()
            except dfwinreg_errors.WinRegistryValueError as exception:
                parser_mediator.ProduceWarning(
                    f"unable to read value: {value_name:s} with error: {exception!s}"
                )
                continue

            if not isinstance(usage_count, int):
                parser_mediator.ProduceWarning(
                    f"unsupported value: {value_name:s} data size: "
                    f"{len(registry_value.data or b''):d}"
                )
                continue

            # The application path can start with a known folder identifier.
            path_segments = value_name.split("\\")
            for segment_index, path_segment in enumerate(path_segments):
                path = known_folders.WindowsKnownFoldersHelper.GetPath(path_segment)
                if path:
                    path_segments[segment_index] = path

            value_name = "\\".join(path_segments)
            if "%" in value_name:
                value_name = parser_mediator.ExpandWindowsPath(value_name)

            entries.append(f"{value_name:s}: {usage_count:d}")

        event_data = FeatureUsageEventData()
        event_data.entries = entries or None
        event_data.key_path = registry_key.path
        event_data.last_written_time = registry_key.last_written_time

        parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugin(FeatureUsagePlugin)
