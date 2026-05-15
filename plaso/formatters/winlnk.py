"""Windows Shortcut (LNK) custom event formatter helpers."""

from plaso.formatters import interface
from plaso.formatters import manager


class WindowsShortcutLinkedPathFormatterHelper(interface.CustomEventFormatterHelper):
    """Windows Shortcut (LNK) linked path formatter helper."""

    IDENTIFIER = "windows_shortcut_linked_path"

    def FormatEventValues(self, output_mediator, event_values):
        """Formats event values using the helper.

        Args:
          output_mediator (OutputMediator): output mediator.
          event_values (dict[str, object]): event values.
        """
        linked_path = event_values.get("local_path")
        if not linked_path:
            linked_path = event_values.get("network_path")

        if not linked_path:
            linked_path = event_values.get("relative_path")
            if linked_path:
                working_directory = event_values.get("working_directory")
                if working_directory:
                    linked_path = "\\".join([working_directory, linked_path])

        event_values["linked_path"] = linked_path or "Unknown"


manager.FormattersManager.RegisterEventFormatterHelper(
    WindowsShortcutLinkedPathFormatterHelper
)
