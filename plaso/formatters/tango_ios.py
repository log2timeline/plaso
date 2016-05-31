# -*- coding: utf-8 -*-
"""Formatter for Tango events from IOS."""
from plaso.formatters import interface
from plaso.formatters import manager

class TangoIOSMessageEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for """
  DATA_TYPE = u'tango:ios:message'

  FORMAT_STRING_PIECES = [
      u'Message: {content}',
      u'']

  FORMAT_STRING_SHORT_PIECES = []

  _MESSAGE_DIRECTION = {
    1: u'Outgoing',
    2: u'Incoming',
  }

  _MESSAGE_TYPE = {

  }


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
    pass

manager.FormattersManager.RegisterFormatter(TangoIOSMessageEventFormatter)