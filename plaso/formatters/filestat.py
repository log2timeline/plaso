# -*- coding: utf-8 -*-
"""This file contains a formatter for the Stat object of a PFile."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class FileStatFormatter(interface.ConditionalEventFormatter):
  """Define the formatting for PFileStat."""

  DATA_TYPE = 'fs:stat'

  FORMAT_STRING_PIECES = [
      u'{display_name}',
      u'({unallocated})']

  FORMAT_STRING_SHORT_PIECES = [u'{filename}']

  SOURCE_SHORT = 'FILE'

  def GetSources(self, event_object):
    """Return a list of source short and long messages."""
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    self.source_string = u'{0:s} {1:s}'.format(
        getattr(event_object, 'fs_type', u'Unknown FS'),
        getattr(event_object, 'timestamp_desc', u'Time'))

    return super(FileStatFormatter, self).GetSources(event_object)

  def GetMessages(self, event_object):
    """Returns a list of messages extracted from an event object.

    Args:
      event_object: The event object (EventObject) containing the event
                    specific data.

    Returns:
      A list that contains both the longer and shorter version of the message
      string.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    if not getattr(event_object, 'allocated', True):
      event_object.unallocated = u'unallocated'

    return super(FileStatFormatter, self).GetMessages(event_object)


manager.FormattersManager.RegisterFormatter(FileStatFormatter)
