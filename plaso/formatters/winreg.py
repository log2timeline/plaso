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
        if isinstance(values, str):
            return

        if not values:
            event_values["values"] = "(empty)"
        else:
            string_parts = []
            for name, data_type, data in sorted(values):
                if not name:
                    name = "(default)"
                if not data:
                    data = "(empty)"
                elif isinstance(data, bytes):
                    data = f"({len(data):d} bytes)"

                string_parts.append(f"{name:s}: [{data_type:s}] {data!s}")

            event_values["values"] = ", ".join(string_parts)


manager.FormattersManager.RegisterEventFormatterHelper(
    WindowsRegistryValuesFormatterHelper
)
