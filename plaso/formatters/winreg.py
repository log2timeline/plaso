"""Windows Registry custom event formatter helpers."""

from plaso.formatters import interface
from plaso.formatters import manager


class WindowsRegistryValuesFormatterHelper(interface.CustomEventFormatterHelper):
    """Windows Registry values formatter helper."""

    IDENTIFIER = "windows_registry_values"

    def FormatEventValues(self, output_mediator, event_values):
        """Formats event values using the helper.

        Args:
          output_mediator (OutputMediator): output mediator.
          event_values (dict[str, object]): event values.
        """
        values = event_values.get("values")
        if not values:
            values_string = "(empty)"

        elif isinstance(values, list):
            value_strings = []
            for name, data_type, data in sorted(values):
                if not name:
                    name = "(default)"
                if not data:
                    data = "(empty)"
                elif isinstance(data, bytes):
                    data = f"({len(data):d} bytes)"

                value_strings.append(f"{name:s}: [{data_type:s}] {data:s}")

            values_string = " ".join(value_strings)

        else:
            values_string = values

        event_values["values"] = values_string


manager.FormattersManager.RegisterEventFormatterHelper(
    WindowsRegistryValuesFormatterHelper
)
