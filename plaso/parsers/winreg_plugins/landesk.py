"""Windows Registry plugin to parse the LANDesk software monitoring keys."""

import os

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class LANDeskSoftwareMonitoringEventData(events.EventData):
    """LANDesk software monitoring event data.

    Attributes:
      first_execution_time (dfdatetime.DateTimeValues): date and time
          the executable (binary) was first executed, provided by the
          "First Started" value.
      key_path (str): Windows Registry key path.
      last_execution_time (dfdatetime.DateTimeValues): date and time
          the executable (binary) was last executed, provided by the
          "Last Started" value.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and
          time.
      number_of_executions (int): number of times the executable (binary) was
          executed, provided by the "Total Runs" value.
      path (str): path of the executable (binary), provided by the key name.
      username (str): name of the user that executed the executable (binary),
          provided by the "Current User" value.
    """

    DATA_TYPE = "windows:registry:landesk:software_monitoring"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.first_execution_time = None
        self.key_path = None
        self.last_execution_time = None
        self.last_written_time = None
        self.number_of_executions = None
        self.path = None
        self.username = None


class LANDeskSoftwareMonitoringPlugin(
    interface.WindowsRegistryPlugin, dtfabric_helper.DtFabricHelper
):
    """LANDesk software monitoring Windows Registry plugin."""

    NAME = "landesk_software_monitoring"
    DATA_FORMAT = "LANDesk software monitoring Registry data"

    FILTERS = frozenset(
        [
            interface.WindowsRegistryKeyPathFilter(
                "HKEY_LOCAL_MACHINE\\Software\\LANDesk\\ManagementSuite\\WinClient\\"
                "SoftwareMonitoring\\MonitorLog"
            )
        ]
    )

    _DEFINITION_FILE = os.path.join(os.path.dirname(__file__), "filetime.yaml")

    def _ParseFiletimeValue(self, parser_mediator, registry_key, value_name):
        """Parses a FILETIME value.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
          value_name (str): name of the value.

        Returns:
          dfdatetime.Filetime: FILETIME date and time value or None if the value
              is not available, does not contain binary data or is not set.
        """
        registry_value = registry_key.GetValueByName(value_name)
        if (
            not registry_value
            or not registry_value.data
            or not registry_value.DataIsBinaryData()
        ):
            return None

        if len(registry_value.data) != 8:
            parser_mediator.ProduceWarning(
                f"unsupported {value_name:s} value data size in key: "
                f"{registry_key.path:s}"
            )
            return None

        timestamp = self._ReadStructureFromByteStream(
            registry_value.data, 0, self._GetDataTypeMap("filetime")
        )

        if not timestamp:
            return None

        return dfdatetime_filetime.Filetime(timestamp=timestamp)

    def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
        """Extracts events from a Windows Registry key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
        """
        for subkey in registry_key.GetSubkeys():
            event_data = LANDeskSoftwareMonitoringEventData()
            event_data.first_execution_time = self._ParseFiletimeValue(
                parser_mediator, subkey, "First Started"
            )
            event_data.key_path = registry_key.path
            event_data.last_execution_time = self._ParseFiletimeValue(
                parser_mediator, subkey, "Last Started"
            )
            event_data.last_written_time = subkey.last_written_time
            event_data.path = subkey.name

            registry_value = subkey.GetValueByName("Total Runs")
            if registry_value and registry_value.DataIsInteger():
                event_data.number_of_executions = registry_value.GetDataAsObject()

            registry_value = subkey.GetValueByName("Current User")
            if registry_value and registry_value.data and registry_value.DataIsString():
                event_data.username = registry_value.GetDataAsObject() or None

            parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugin(LANDeskSoftwareMonitoringPlugin)
