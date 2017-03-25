# -*- coding: utf-8 -*-
"""This file contains the shell item specific event object classes."""

from plaso.containers import time_events


class ShellItemFileEntryEvent(time_events.DateTimeValuesEvent):
  """Convenience class for a shell item file entry event.

  Attributes:
    name (str): name of the file entry shell item.
    long_name (str): long name of the file entry shell item.
    localized_name (str): localized name of the file entry shell item.
    file_reference (str): NTFS file reference, in the format:
        "MTF entry - sequence number".
    shell_item_path (str): shell item path.
    origin (str): origin of the event.
  """

  DATA_TYPE = u'windows:shell_item:file_entry'

  def __init__(
      self, date_time, date_time_description, name, long_name, localized_name,
      file_reference, shell_item_path, origin):
    """Initializes an event object.

    Args:
      date_time (dfdatetime.DateTimeValues): date and time values.
      date_time_description (str): description of the meaning of the date
          and time values.
      name (str): name of the file entry shell item.
      long_name (str): long name of the file entry shell item.
      localized_name (str): localized name of the file entry shell item.
      file_reference (str): NTFS file reference, in the format:
          "MTF entry - sequence number".
      shell_item_path (str): shell item path.
      origin (str): origin of the event.
    """
    super(ShellItemFileEntryEvent, self).__init__(
        date_time, date_time_description)
    self.file_reference = file_reference
    self.localized_name = localized_name
    self.long_name = long_name
    self.name = name
    self.origin = origin
    self.shell_item_path = shell_item_path
