# -*- coding: utf-8 -*-
"""The file system stat event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class FileStatFormatter(interface.ConditionalEventFormatter):
  """The file system stat event formatter."""

  DATA_TYPE = 'fs:stat'

  FORMAT_STRING_PIECES = [
      u'{display_name}',
      u'({unallocated})']

  FORMAT_STRING_SHORT_PIECES = [
      u'{filename}']

  SOURCE_SHORT = 'FILE'

  def GetMessages(self, unused_formatter_mediator, event_object):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator: the formatter mediator object (instance of
                          FormatterMediator).
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple containing the formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    event_values = event_object.GetValues()
    if not event_values.get(u'allocated', False):
      event_values[u'unallocated'] = u'unallocated'

    return self._ConditionalFormatMessages(event_values)

  def GetSources(self, event_object):
    """Determines the the short and long source for an event object.

    Args:
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple of the short and long source string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    fs_type = getattr(event_object, u'fs_type', u'Unknown FS')
    timestamp_desc = getattr(event_object, u'timestamp_desc', u'Time')
    source_long = u'{0:s} {1:s}'.format(fs_type, timestamp_desc)

    return self.SOURCE_SHORT, source_long


manager.FormattersManager.RegisterFormatter(FileStatFormatter)
