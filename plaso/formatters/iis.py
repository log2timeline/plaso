# -*- coding: utf-8 -*-
"""The Microsoft IIS log file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class IISLogFileEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Microsoft IIS log file event."""

  DATA_TYPE = 'iis:log:line'

  FORMAT_STRING_PIECES = [
      '{http_method}',
      '{requested_uri_stem}',
      '[',
      '{source_ip}',
      '>',
      '{dest_ip}',
      ':',
      '{dest_port}',
      ']',
      'HTTP Status: {http_status}',
      'Bytes Sent: {sent_bytes}',
      'Bytes Received: {received_bytes}',
      'User Agent: {user_agent}',
      'Protocol Version: {protocol_version}']

  FORMAT_STRING_SHORT_PIECES = [
      '{http_method}',
      '{requested_uri_stem}',
      '[',
      '{source_ip}',
      '>',
      '{dest_ip}',
      ':',
      '{dest_port}',
      ']']

  SOURCE_LONG = 'IIS Log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(IISLogFileEventFormatter)
