# -*- coding: utf-8 -*-
"""This file contains the shell item specific event object classes."""

from plaso.events import time_events


class ShellItemFileEntryEvent(time_events.FatDateTimeEvent):
  """Convenience class for a shell item file entry event."""

  DATA_TYPE = 'windows:shell_item:file_entry'

  def __init__(
      self, fat_date_time, usage, name, long_name, localized_name,
      file_reference, origin):
    """Initializes an event object.

    Args:
      fat_date_time: The FAT date time value.
      usage: The description of the usage of the time value.
      name: A string containing the name of the file entry shell item.
      long_name: A string containing the long name of the file entry shell item.
      localized_name: A string containing the localized name of the file entry
                      shell item.
      file_reference: A string containing the NTFS file reference
                      (MTF entry - sequence number).
      origin: A string containing the origin of the event (event source).
    """
    super(ShellItemFileEntryEvent, self).__init__(fat_date_time, usage)

    self.name = name
    self.long_name = long_name
    self.localized_name = localized_name
    self.file_reference = file_reference
    self.origin = origin
