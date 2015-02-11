# -*- coding: utf-8 -*-
"""Formatter for Hachoir events."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


__author__ = 'David Nides (david.nides@gmail.com)'


class HachoirFormatter(interface.EventFormatter):
  """Formatter for Hachoir based events."""

  DATA_TYPE = 'metadata:hachoir'
  FORMAT_STRING = u'{data}'

  SOURCE_LONG = 'Hachoir Metadata'
  SOURCE_SHORT = 'META'

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

    string_parts = []
    for key, value in sorted(event_object.metadata.items()):
      string_parts.append(u'{0:s}: {1:s}'.format(key, value))

    event_object.data = u' '.join(string_parts)

    return super(HachoirFormatter, self).GetMessages(event_object)


manager.FormattersManager.RegisterFormatter(HachoirFormatter)
