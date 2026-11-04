"""This file contains the MSIE zone settings plugin."""

from plaso.containers import events
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class MSIEZoneSettingsEventData(events.EventData):
    """MSIE zone settings event data attribute container.

    Attributes:
      key_path (str): Windows Registry key path.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and time.
      settings (list[tuple[str, object]]): MSIE zone settings.
    """

    DATA_TYPE = "windows:registry:msie_zone_settings"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.key_path = None
        self.last_written_time = None
        self.settings = None


class MSIEZoneSettingsPlugin(interface.WindowsRegistryPlugin):
    """Windows Registry plugin for parsing the MSIE zone settings.

    The MSIE Feature controls are stored in the Zone specific subkeys in:
      Internet Settings\\Zones key
      Internet Settings\\Lockdown_Zones key
    """

    NAME = "msie_zone"
    DATA_FORMAT = "Microsoft Internet Explorer zone settings Registry data"

    FILTERS = frozenset(
        [
            interface.WindowsRegistryKeyPathFilter(
                "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\"
                "Internet Settings\\Lockdown_Zones"
            ),
            interface.WindowsRegistryKeyPathFilter(
                "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\"
                "Internet Settings\\Zones"
            ),
            interface.WindowsRegistryKeyPathFilter(
                "HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\"
                "Internet Settings\\Lockdown_Zones"
            ),
            interface.WindowsRegistryKeyPathFilter(
                "HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\"
                "Internet Settings\\Zones"
            ),
        ]
    )

    _ZONE_NAMES = {
        "0": "0 (My Computer)",
        "1": "1 (Local Intranet Zone)",
        "2": "2 (Trusted sites Zone)",
        "3": "3 (Internet Zone)",
        "4": "4 (Restricted Sites Zone)",
        "5": "5 (Custom)",
    }

    def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
        """Extracts events from a Windows Registry key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
        """
        self._ProduceDefaultWindowsRegistryEvent(parser_mediator, registry_key)

        if registry_key.number_of_subkeys == 0:
            parser_mediator.ProduceWarning(
                f"Key: {registry_key.path:s} missing subkeys."
            )
            return

        for zone_key in registry_key.GetSubkeys():
            # TODO: these values are stored in the Description value of the
            # zone key. This solution will break on zone values that are larger
            # than 5.
            path = "\\".join([registry_key.path, self._ZONE_NAMES[zone_key.name]])

            corrupted = False
            settings = []

            # TODO: this plugin currently just dumps the values and does not distinguish
            # between what is a feature control or not.
            for value in zone_key.GetValues():
                # TODO: add support to parse first and third party cookie values.
                if not value.name or value.name in (
                    "{A8A88C49-5EB2-4990-A1A2-0876022C854F}",  # Third Party Cookie
                    "{AEBA21FA-782A-4A90-978D-B72164C80120}",  # First Party Cookie
                ):
                    continue

                if value.DataIsString():
                    value_object = value.GetDataAsObject()

                elif value.DataIsInteger():
                    value_object = value.GetDataAsObject()

                else:
                    parser_mediator.ProduceWarning(
                        f"unable to extract MSIE zone setting: '{value.name:s}' from: "
                        f"'{zone_key.path:s}' unsupported value data type: "
                        f"'{value.data_type_string:s}'"
                    )
                    corrupted = True
                    continue

                settings.append((value.name, value_object))

            event_data = MSIEZoneSettingsEventData()
            event_data.key_path = path
            event_data.last_written_time = zone_key.last_written_time
            event_data.settings = sorted(settings)

            parser_mediator.ProduceEventData(event_data, corrupted=corrupted)


winreg_parser.WinRegistryParser.RegisterPlugin(MSIEZoneSettingsPlugin)
