# -*- coding: utf-8 -*-
"""The Apple System Log (ASL) event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors
from plaso.lib import py2to3


class ASLFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Apple System Log (ASL) log event."""

  DATA_TYPE = 'mac:asl:event'

  FORMAT_STRING_PIECES = [
      'MessageID: {message_id}',
      'Level: {level}',
      'User ID: {user_sid}',
      'Group ID: {group_id}',
      'Read User: {read_uid}',
      'Read Group: {read_gid}',
      'Host: {computer_name}',
      'Sender: {sender}',
      'Facility: {facility}',
      'Message: {message}',
      '{extra_information}']

  FORMAT_STRING_SHORT_PIECES = [
      'Host: {host}',
      'Sender: {sender}',
      'Facility: {facility}']

  SOURCE_LONG = 'ASL entry'
  SOURCE_SHORT = 'LOG'

  # Priority levels (criticality)
  _PRIORITY_LEVELS = {
      0 : 'EMERGENCY',
      1 : 'ALERT',
      2 : 'CRITICAL',
      3 : 'ERROR',
      4 : 'WARNING',
      5 : 'NOTICE',
      6 : 'INFO',
      7 : 'DEBUG'}

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions
          between formatters and other components, such as storage and Windows
          EventLog resources.
      event_data (EventData): event data.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_data.data_type))

    event_values = event_data.CopyToDict()

    priority_level = event_values.get('level', None)
    if isinstance(priority_level, py2to3.INTEGER_TYPES):
      event_values['level'] = '{0:s} ({1:d})'.format(
          self._PRIORITY_LEVELS.get(priority_level, 'UNKNOWN'), priority_level)

    # If no rights are assigned the value is 0xffffffff (-1).
    read_uid = event_values.get('read_uid', None)
    if read_uid == -1:
      event_values['read_uid'] = 'ALL'

    # If no rights are assigned the value is 0xffffffff (-1).
    read_gid = event_values.get('read_gid', None)
    if read_gid == -1:
      event_values['read_gid'] = 'ALL'

    # TODO: get the real name for the user of the group having the uid or gid.
    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(ASLFormatter)
