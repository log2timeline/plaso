# -*- coding: utf-8 -*-
"""The Apple System Log (ASL) event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors
from plaso.lib import py2to3


class ASLFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Apple System Log (ASL) log event."""

  DATA_TYPE = u'mac:asl:event'

  FORMAT_STRING_PIECES = [
      u'MessageID: {message_id}',
      u'Level: {level}',
      u'User ID: {user_sid}',
      u'Group ID: {group_id}',
      u'Read User: {read_uid}',
      u'Read Group: {read_gid}',
      u'Host: {computer_name}',
      u'Sender: {sender}',
      u'Facility: {facility}',
      u'Message: {message}',
      u'{extra_information}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Host: {host}',
      u'Sender: {sender}',
      u'Facility: {facility}']

  SOURCE_LONG = u'ASL entry'
  SOURCE_SHORT = u'LOG'

  # Priority levels (criticality)
  _PRIORITY_LEVELS = {
      0 : u'EMERGENCY',
      1 : u'ALERT',
      2 : u'CRITICAL',
      3 : u'ERROR',
      4 : u'WARNING',
      5 : u'NOTICE',
      6 : u'INFO',
      7 : u'DEBUG'}

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

    event_values = event_object.CopyToDict()

    priority_level = event_values.get(u'level', None)
    if isinstance(priority_level, py2to3.INTEGER_TYPES):
      event_values[u'level'] = u'{0:s} ({1:d})'.format(
          self._PRIORITY_LEVELS.get(priority_level, u'UNKNOWN'), priority_level)

    # If no rights are assigned the value is 0xffffffff (-1).
    read_uid = event_values.get(u'read_uid', None)
    if read_uid == 0xffffffff:
      event_values[u'read_uid'] = u'ALL'

    # If no rights are assigned the value is 0xffffffff (-1).
    read_gid = event_values.get(u'read_gid', None)
    if read_gid == 0xffffffff:
      event_values[u'read_gid'] = u'ALL'

    # TODO: get the real name for the user of the group having the uid or gid.
    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(ASLFormatter)
