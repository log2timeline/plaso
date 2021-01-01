# -*- coding: utf-8 -*-
"""Shell item event attribute container."""

from plaso.containers import events


class ShellItemFileEntryEventData(events.EventData):
  """Shell item file entry event data attribute container.

  Attributes:
    name (str): name of the file entry shell item.
    long_name (str): long name of the file entry shell item.
    localized_name (str): localized name of the file entry shell item.
    file_reference (str): NTFS file reference, in the format:
        "MTF entry - sequence number".
    shell_item_path (str): shell item path.
    origin (str): origin of the event.
  """

  DATA_TYPE = 'windows:shell_item:file_entry'

  def __init__(self):
    """Initializes event data."""
    super(ShellItemFileEntryEventData, self).__init__(data_type=self.DATA_TYPE)
    self.file_reference = None
    self.localized_name = None
    self.long_name = None
    self.name = None
    self.origin = None
    self.shell_item_path = None
