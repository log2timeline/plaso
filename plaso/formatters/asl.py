# -*- coding: utf-8 -*-
"""Formatter for the Apple System Log binary files."""

from plaso.formatters import interface
from plaso.formatters import manager


class AslFormatter(interface.ConditionalEventFormatter):
  """Formatter for an ASL log entry."""

  DATA_TYPE = 'mac:asl:event'

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

  SOURCE_LONG = 'ASL entry'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(AslFormatter)
