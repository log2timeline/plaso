# -*- coding: utf-8 -*-
"""The Microsoft IIS log file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


__author__ = 'Ashley Holtz (ashley.a.holtz@gmail.com)'


class IISLogFileEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Microsoft IIS log file event."""

  DATA_TYPE = u'iis:log:line'

  FORMAT_STRING_PIECES = [
      u'{http_method}',
      u'{requested_uri_stem}',
      u'[',
      u'{source_ip}',
      u'>',
      u'{dest_ip}',
      u':',
      u'{dest_port}',
      u']',
      u'HTTP Status: {http_status}',
      u'Bytes Sent: {sent_bytes}',
      u'Bytes Received: {received_bytes}',
      u'User Agent: {user_agent}',
      u'Protocol Version: {protocol_version}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{http_method}',
      u'{requested_uri_stem}',
      u'[',
      u'{source_ip}',
      u'>',
      u'{dest_ip}',
      u':',
      u'{dest_port}',
      u']']

  SOURCE_LONG = u'IIS Log'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatter(IISLogFileEventFormatter)
