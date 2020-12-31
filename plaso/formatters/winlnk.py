# -*- coding: utf-8 -*-
"""Windows Shortcut (LNK) custom event formatter helpers."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class WinLnkLinkFormatter(interface.CustomEventFormatterHelper):
  """Custom formatter for Windows Shortcut (LNK) link event values."""

  DATA_TYPE = 'windows:lnk:link'

  def FormatEventValues(self, event_values):
    """Formats event values using the helper.

    Args:
      event_values (dict[str, object]): event values.
    """
    if 'description' not in event_values:
      event_values['description'] = 'Empty description'

    linked_path = event_values.get('local_path', None)
    if not linked_path:
      linked_path = event_values.get('network_path', None)

    if not linked_path:
      linked_path = event_values.get('relative_path', None)
      if linked_path:
        working_directory = event_values.get('working_directory', None)
        if working_directory:
          linked_path = '\\'.join([working_directory, linked_path])

    event_values['linked_path'] = linked_path or 'Unknown'


manager.FormattersManager.RegisterEventFormatterHelper(WinLnkLinkFormatter)
